"""EEPROM microcode CW store — fit-study model (not v1.0 SoC path)."""

from __future__ import annotations

from simulators.cyclesim.data.fsm_table import FSM_ROWS, idx5_index

# Reuse production CW bit maps without importing cpld_fsm.hdl package
CW_LO_BITS: tuple[str, ...] = (
    "mem_rd",
    "mem_wr",
    "y_oe",
    "flg_we",
    "pc_load_en",
    "cin",
    "bctrl0",
    "bctrl2",
)
CW_HI_BITS: tuple[str, ...] = (
    "lgc0",
    "lgc1",
    "lgc2",
    "lgc3",
    "s0",
    "s1",
)


def _pack(bits: tuple[str, ...], merged: dict[str, bool]) -> int:
    value = 0
    for i, name in enumerate(bits):
        if merged.get(name, False):
            value |= 1 << i
    return value


def merged_strobes_for_row(row) -> dict[str, bool]:
    """Row → merged strobes including bctrl fanout and pc_load for EEPROM pack."""
    b0 = bool((row.alu.bctrl >> 0) & 1)
    b2 = bool((row.alu.bctrl >> 2) & 1)
    return {
        "mem_rd": row.mem_rd,
        "mem_wr": row.mem_wr,
        "y_oe": row.y_oe,
        "flg_we": row.flg_we,
        "pc_load_en": row.pc_load_en,
        "cin": bool(row.alu.cin),
        "bctrl0": b0,
        "bctrl1": b0,
        "bctrl2": b2,
        "bctrl3": b2,
        "lgc0": bool((row.alu.lgc >> 0) & 1),
        "lgc1": bool((row.alu.lgc >> 1) & 1),
        "lgc2": bool((row.alu.lgc >> 2) & 1),
        "lgc3": bool((row.alu.lgc >> 3) & 1),
        "s0": bool(row.alu.s0),
        "s1": bool(row.alu.s1),
    }


class EepromCtrlStore:
    """128 idx5 slots × 2 bytes (LO/HI). Inactive slots read 0x00."""

    def __init__(self) -> None:
        self._lo = [0] * 128
        self._hi = [0] * 128
        for row in FSM_ROWS:
            idx = idx5_index(row.opcode, row.phase)
            m = merged_strobes_for_row(row)
            self._lo[idx] = _pack(CW_LO_BITS, m)
            self._hi[idx] = _pack(CW_HI_BITS, m)

    def lookup(self, opcode: int, phase: int) -> tuple[int, int]:
        idx = idx5_index(opcode, phase)
        return self._lo[idx], self._hi[idx]

    def read_bus_byte(self, opcode: int, phase: int, bank: int) -> int:
        lo, hi = self.lookup(opcode, phase)
        return lo if bank == 0 else hi

    def image_bytes(self) -> bytes:
        """Linear 256 B image: index*2=LO, index*2+1=HI."""
        out = bytearray(256)
        for idx in range(128):
            out[idx * 2] = self._lo[idx]
            out[idx * 2 + 1] = self._hi[idx]
        return bytes(out)
