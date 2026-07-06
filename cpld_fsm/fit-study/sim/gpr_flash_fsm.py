"""E1 integrated model — CPLD GPR + EEPROM CW + TFR comb (fit-study)."""

from __future__ import annotations

from simulators.cyclesim.data.isa import decode_tfr, is_tfr_valid
from simulators.cyclesim.data.fsm_table import FSM_ROWS, idx5_index

from .eeprom_cw import CW_HI_BITS, CW_LO_BITS, EepromCtrlStore


class InternalGpr:
    """Three 8-bit registers with fixed q_a=R0, q_b=R1."""

    def __init__(self) -> None:
        self.regs = [0, 0, 0]

    def read(self, sel: int) -> int:
        return self.regs[sel & 3] & 0xFF if sel < 3 else 0

    def write(self, w_sel: int, data: int, reg_we: bool) -> None:
        if reg_we and 0 <= w_sel <= 2:
            self.regs[w_sel] = data & 0xFF

    @property
    def q_a(self) -> int:
        return self.regs[0]

    @property
    def q_b(self) -> int:
        return self.regs[1]


def tfr_strobes(opcode: int) -> tuple[bool, int]:
    """E1b comb: reg_we + w_sel(dst) from opcode."""
    if not is_tfr_valid(opcode):
        return False, 0
    _src, dst = decode_tfr(opcode)
    return True, dst


def tfr_xfer_data(gpr: InternalGpr, opcode: int) -> int:
    if not is_tfr_valid(opcode):
        return 0
    src, _dst = decode_tfr(opcode)
    return gpr.read(src)


class E1GprEepromModel:
    """Single-cycle TFR + EEPROM CW lookup per idx5 slot."""

    def __init__(self) -> None:
        self.gpr = InternalGpr()
        self.eeprom = EepromCtrlStore()
        self.opcode = 0
        self.phase = 0
        self.d_bus = 0

    def cw_bytes(self) -> tuple[int, int]:
        return self.eeprom.lookup(self.opcode, self.phase)

    def cw_strobes(self) -> dict[str, bool]:
        lo, hi = self.cw_bytes()
        out: dict[str, bool] = {}
        for i, name in enumerate(CW_LO_BITS):
            out[name] = bool((lo >> i) & 1)
        for i, name in enumerate(CW_HI_BITS):
            out[name] = bool((hi >> i) & 1)
        return out

    def execute_tfr(self, opcode: int) -> None:
        """One-phase TFR (E1b): xfer mux + reg_we."""
        we, dst = tfr_strobes(opcode)
        if not we:
            return
        data = tfr_xfer_data(self.gpr, opcode)
        self.gpr.write(dst, data, True)

    def execute_lda_phase(self, opcode: int, phase: int, d_bus: int) -> None:
        """LDA ph1: load R0 from bus (non-TFR macro write)."""
        if phase != 1 or (opcode & 0x1F) != 0x02:
            return
        strobes = self.eeprom.lookup(opcode, phase)
        lo = strobes[0]
        # reg_we/w_sel from EEPROM CW in full SoC — model direct R0 load
        if lo & 0x01:  # mem_rd active row; still write R0 on LDA ph1
            self.gpr.write(0, d_bus, True)

    def parity_fsm_row(self, opcode: int, phase: int) -> bool:
        """EEPROM LO/HI packs match golden for active rows."""
        for row in FSM_ROWS:
            if row.opcode == opcode and row.phase == phase:
                lo, hi = self.eeprom.lookup(opcode, phase)
                from cpld_fsm.hdl.fsm_golden import merged_for_cw_pack, pack_cw_hi, pack_cw_lo

                m = merged_for_cw_pack(opcode, phase, macro_end=True, flg_z=True)
                return lo == pack_cw_lo(m) and hi == pack_cw_hi(m)
        return self.eeprom.lookup(opcode, phase) == (0, 0)
