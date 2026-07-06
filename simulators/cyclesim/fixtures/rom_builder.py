"""Build machine-code ROM images for cyclesim tests."""

from __future__ import annotations

OP_LDA = 0x02
OP_STA = 0x03
OP_ADD = 0x01
OP_CMP = 0x0D
OP_BEQ = 0x04
OP_JMP = 0x05
OP_HALT = 0x0A

# Gi1 unrolled fib ROM must fit addr8 RAM cells above image (max limit ≈232).
FIB_LIMIT = 232

# Set by build_fib_to_limit_rom — RAM cells sit above the ROM image (see below).
ADDR_FIB_A: int | None = None
ADDR_FIB_B: int | None = None


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


def fib_pairs_to_limit(limit: int = FIB_LIMIT) -> list[tuple[int, int]]:
    """All (a, b) pairs from init through largest term <= limit."""
    target, _ = last_fib_leq(limit)
    pairs: list[tuple[int, int]] = []
    a, b = 0, 1
    pairs.append((a, b))
    while b < target:
        a, b = b, a + b
        pairs.append((a, b))
    return pairs


def _insn_length(op: int) -> int:
    if op in (OP_BEQ, OP_JMP):
        return 3
    if op == OP_HALT or (op & 0x10) == 0x10:
        return 1
    return 2


def _operand_fetch_pcs(rom: bytes) -> set[int]:
    """PC positions where fetch reads an operand byte (map_mode=1 RAM mirror)."""
    pcs: set[int] = set()
    pc = 0
    while pc < len(rom):
        op = rom[pc]
        ilen = _insn_length(op)
        for off in range(1, ilen):
            pcs.add(pc + off)
        pc += ilen
    return pcs


def _emit_fib_body(rb: RomBuilder, fa: int, fb: int, tmp: int, target: int, limit: int) -> None:
    """Gi1 Fibonacci step — temp RAM cell; no TFR."""
    a, bb = 0, 1
    while True:
        rb.lda(fb)
        rb.cmp(target)
        rb.beq("halt")
        if bb == target:
            break

        rb.lda(fb)
        rb.sta(tmp)
        rb.lda(fa)
        rb.add(bb)
        rb.sta(fb)
        rb.lda(tmp)
        rb.sta(fa)

        a, bb = bb, a + bb

    rb.label("halt")
    rb.halt()


def build_fib_to_limit_rom(limit: int = FIB_LIMIT) -> tuple[bytes, dict[int, int], int]:
    """
    ROM: advance Fibonacci in RAM until b equals the largest term <= limit.

    Gi1 step (tmp holds previous b):
      LDA fb; STA tmp
      LDA fa; ADD #bb; STA fb
      LDA tmp; STA fa

    RAM cells are placed immediately above the ROM image (addr8) so operand
    fetches never alias live data under map_mode=1.
    """
    global ADDR_FIB_A, ADDR_FIB_B

    target, _next = last_fib_leq(limit)

    probe = RomBuilder(0x0000)
    _emit_fib_body(probe, 0xF0, 0xF1, 0xF2, target, limit)
    data_base = len(probe.to_bytes())

    fa = data_base
    fb = data_base + 1
    tmp = data_base + 2
    if tmp > 0xFF:
        raise ValueError(
            f"fib ROM {data_base} bytes — Gi1 sequence exceeds addr8; "
            f"lower FIB_LIMIT (max fits ~200)"
        )

    rb = RomBuilder(0x0000)
    _emit_fib_body(rb, fa, fb, tmp, target, limit)
    rom = rb.to_bytes()
    assert len(rom) == data_base

    fetches = _operand_fetch_pcs(rom)
    if fetches.intersection({fa, fb, tmp}):
        raise ValueError("fib RAM aliases operand-fetch PCs — adjust layout")

    ADDR_FIB_A = fa
    ADDR_FIB_B = fb
    ram_init = {fa: 0, fb: 1}
    return rom, ram_init, target


def build_fib_250_rom() -> tuple[bytes, dict[int, int]]:
    """Fibonacci up to largest term <= FIB_LIMIT."""
    rom, ram, _ = build_fib_to_limit_rom(FIB_LIMIT)
    return rom, ram
