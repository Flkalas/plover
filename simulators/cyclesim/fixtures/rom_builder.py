"""Build machine-code ROM images for cyclesim tests."""

from __future__ import annotations

OP_LDA = 0x02
OP_STA = 0x03
OP_ADD = 0x01
OP_CMP = 0x0D
OP_BEQ = 0x04
OP_JMP = 0x05
OP_HALT = 0x0A
TFR01 = 0x11  # R1 -> R0
TFR02 = 0x12  # R2 -> R0

ADDR_FIB_A = 0x80
ADDR_FIB_B = 0x81

# Largest Fibonacci number not exceeding this limit (8-bit path stays < 256 until stop).
FIB_LIMIT = 250


class RomBuilder:
    def __init__(self, base: int = 0) -> None:
        self.bytes: dict[int, int] = {}
        self.pc = base
        self._fixups: list[tuple[int, str]] = []
        self.labels: dict[str, int] = {}

    def label(self, name: str) -> int:
        self.labels[name] = self.pc
        return self.pc

    def _emit(self, *vals: int) -> int:
        start = self.pc
        for v in vals:
            self.bytes[self.pc] = v & 0xFF
            self.pc += 1
        return start

    def lda(self, addr: int) -> int:
        return self._emit(OP_LDA, addr & 0xFF)

    def sta(self, addr: int) -> int:
        return self._emit(OP_STA, addr & 0xFF)

    def add(self, imm: int) -> int:
        return self._emit(OP_ADD, imm & 0xFF)

    def cmp(self, imm: int) -> int:
        return self._emit(OP_CMP, imm & 0xFF)

    def jmp(self, target: str) -> int:
        pos = self._emit(OP_JMP, 0, 0)
        self._fixups.append((pos + 1, target))
        return pos

    def beq(self, target: str) -> int:
        pos = self._emit(OP_BEQ, 0, 0)
        self._fixups.append((pos + 1, target))
        return pos

    def tfr(self, op: int) -> int:
        return self._emit(op)

    def halt(self) -> int:
        return self._emit(OP_HALT)

    def resolve(self) -> None:
        for pos, name in self._fixups:
            target = self.labels[name]
            self.bytes[pos] = target & 0xFF
            self.bytes[pos + 1] = (target >> 8) & 0xFF

    def to_bytes(self) -> bytes:
        self.resolve()
        if not self.bytes:
            return b""
        end = max(self.bytes) + 1
        out = bytearray(end)
        for i, v in self.bytes.items():
            out[i] = v
        return bytes(out)


def last_fib_leq(limit: int) -> tuple[int, int]:
    """Return (largest_fib, next_fib) where largest_fib <= limit < next_fib."""
    a, b = 0, 1
    while b <= limit:
        a, b = b, a + b
    return a, b


def fib_pair_before_target(limit: int = FIB_LIMIT) -> tuple[int, int]:
    """Return (a, b) RAM pair when b reaches largest Fibonacci term <= limit."""
    target, _ = last_fib_leq(limit)
    a, b = 0, 1
    while b < target:
        a, b = b, a + b
    return a, b


def build_fib_to_limit_rom(limit: int = FIB_LIMIT) -> tuple[bytes, dict[int, int], int]:
    """
    ROM: advance Fibonacci in RAM until b equals the largest term <= limit.

    Each step: new_a = b, new_b = a + b via ADD imm (imm = current b, codegen-unrolled).
    """
    target, _next = last_fib_leq(limit)
    rb = RomBuilder(0x0000)
    ram_init = {ADDR_FIB_A: 0, ADDR_FIB_B: 1}

    a, bb = 0, 1
    while True:
        rb.lda(ADDR_FIB_B)
        rb.cmp(target)
        rb.beq("halt")
        if bb == target:
            break

        rb.lda(ADDR_FIB_A)
        rb.add(bb)
        rb.tfr(TFR01)
        rb.sta(ADDR_FIB_A)
        rb.tfr(TFR02)
        rb.sta(ADDR_FIB_B)

        a, bb = bb, a + bb

    rb.label("halt")
    rb.halt()

    return rb.to_bytes(), ram_init, target


def build_fib_250_rom() -> tuple[bytes, dict[int, int]]:
    """Fibonacci up to 250 (largest term 233)."""
    rom, ram, _ = build_fib_to_limit_rom(FIB_LIMIT)
    return rom, ram
