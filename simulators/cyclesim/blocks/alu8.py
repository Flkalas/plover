"""8-bit ALU composed of MUX4 slices, ADD4, MUX2, and CMP flags."""

from __future__ import annotations

from dataclasses import dataclass

from simulators.cyclesim.blocks.adder import add8
from simulators.cyclesim.blocks.mux import mux4, mux2


@dataclass(frozen=True)
class AluControls:
    cin: int = 0
    bctrl: int = 0
    lgc: int = 0
    s0: int = 0
    s1: int = 0

    @property
    def y_mux_sel(self) -> int:
        return self.s0 | self.s1


# Normative macro ALU ops (control-and-decode.md)
ALU_NOP = AluControls(cin=0, bctrl=0b0000, lgc=0b0000, s0=0, s1=0)
ALU_ADD = AluControls(cin=0, bctrl=0b1100, lgc=0b0000, s0=0, s1=0)
ALU_SUB = AluControls(cin=1, bctrl=0b0011, lgc=0b0000, s0=0, s1=0)
ALU_CMP = ALU_SUB


def _b_add_bit(a_i: int, b_i: int, bctrl: int) -> int:
    """Mux2 B-path for shared bctrl pattern (alu8-phase-b.md)."""
    if bctrl == 0b1100:
        return b_i
    if bctrl == 0b0011:
        return 1 - b_i
    if bctrl == 0b1111:
        return 1
    return 0


def _logic_bit(a_i: int, b_i: int, lgc: int, s0: int, s1: int) -> int:
    if s0 or s1:
        sel = (s1 << 1) | s0
    else:
        sel = a_i | (b_i << 1)
    c0 = (lgc >> 0) & 1
    c1 = (lgc >> 1) & 1
    c2 = (lgc >> 2) & 1
    c3 = (lgc >> 3) & 1
    return mux4(sel, c0, c1, c2, c3)


@dataclass
class AluResult:
    y: int
    z: bool
    c_hi: int


def eval_alu8(a: int, b: int, ctrl: AluControls) -> AluResult:
    """Evaluate 8-bit ALU from functional blocks (b3-opcode golden vectors)."""
    b_add = 0
    logic = 0
    for i in range(8):
        ai = (a >> i) & 1
        bi = (b >> i) & 1
        b_add |= _b_add_bit(ai, bi, ctrl.bctrl) << i
        logic |= _logic_bit(ai, bi, ctrl.lgc, ctrl.s0, ctrl.s1) << i

    sum_y, c_hi = add8(a, b_add, ctrl.cin)

    if ctrl.y_mux_sel:
        y = logic
        c_hi = 0
    else:
        y = sum_y

    return AluResult(y=y & 0xFF, z=(y & 0xFF) == 0, c_hi=c_hi)


class Alu8:
    """Structural ALU block wired into SimContext nets."""

    def __init__(self, name: str = "alu8") -> None:
        self.name = name

    def read_ctrl(self, ctx) -> AluControls:
        def nib(name: str) -> int:
            v = 0
            for i in range(4):
                v |= (ctx.get(f"net_{name}{i}") & 1) << i
            return v

        return AluControls(
            cin=ctx.get("net_cin") & 1,
            bctrl=nib("bctrl"),
            lgc=nib("lgc"),
            s0=ctx.get("net_153_s0") & 1,
            s1=ctx.get("net_153_s1") & 1,
        )

    def eval(self, ctx, a: int, b: int) -> AluResult:
        return eval_alu8(a, b, self.read_ctrl(ctx))

    def drive_outputs(self, ctx, res: AluResult) -> None:
        for i in range(8):
            ctx.drive(f"net_y{i}", (res.y >> i) & 1, self.name)
        ctx.drive("net_cmp_z", 1 if res.z else 0, self.name)
        ctx.drive("net_c_hi", res.c_hi & 1, self.name)
