"""External 574×3 GPR — fit-study model (A1)."""

from __future__ import annotations


class ExternalGpr574:
    """Three 8-bit registers with fixed read ports R0→q_a, R1→q_b."""

    def __init__(self) -> None:
        self.regs = [0, 0, 0]

    def write(self, w_sel: int, data: int, reg_we: bool) -> None:
        if reg_we and 0 <= w_sel <= 2:
            self.regs[w_sel] = data & 0xFF

    @property
    def q_a(self) -> int:
        return self.regs[0]

    @property
    def q_b(self) -> int:
        return self.regs[1]

    def read_reg(self, index: int) -> int:
        return self.regs[index & 3] if index < 3 else 0
