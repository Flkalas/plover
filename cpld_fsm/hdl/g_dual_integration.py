"""G Plan dual CPLD integration models — rev G production golden."""

from __future__ import annotations

from dataclasses import dataclass, field

from simulators.cyclesim.data.isa import TFR_OPS, decode_tfr, is_tfr_valid


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


@dataclass(frozen=True)
class GicStrobes:
    reg_we: bool
    w_sel: int
    tfr_valid: bool
    src: int


@dataclass
class GPlanCuModel:
    """CPLD-CU: opcode → G-IC strobes (matches system_ctrl_cu.pld merge)."""

    def decode_g_ic(self, opcode: int, *, reg_we_lut: bool = False, w_sel_lut: int = 0) -> GicStrobes:
        op = opcode & 0x1F
        if is_tfr_valid(op):
            src, dst = decode_tfr(op)
            return GicStrobes(reg_we=True, w_sel=dst, tfr_valid=True, src=src)
        return GicStrobes(
            reg_we=reg_we_lut,
            w_sel=w_sel_lut & 0x3,
            tfr_valid=False,
            src=0,
        )

    def tfr_valid(self, opcode: int) -> bool:
        return is_tfr_valid(opcode & 0x1F)


@dataclass
class GPlanDpModel:
    """CPLD-DP: GPR + production-style TFR src mux via G-IC src[1:0]."""

    gpr: InternalGpr = field(default_factory=InternalGpr)

    def apply_g_ic(self, strobes: GicStrobes, d_in: int = 0) -> None:
        if not strobes.reg_we:
            return
        if strobes.tfr_valid:
            data = self.gpr.read(strobes.src)
            self.gpr.write(strobes.w_sel, data, True)
        else:
            self.gpr.write(strobes.w_sel, d_in, True)

    def execute_tfr_opcode(self, opcode: int, cu: GPlanCuModel | None = None) -> None:
        cu = cu or GPlanCuModel()
        self.apply_g_ic(cu.decode_g_ic(opcode))


def all_v10_tfr_golden() -> dict[int, tuple[int, int]]:
    """opcode -> (src_reg, dst_reg) for six normative TFR ops."""
    return {op: decode_tfr(op) for op in TFR_OPS}
