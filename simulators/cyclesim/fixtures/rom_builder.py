"""Build machine-code ROM images for cyclesim tests."""

from __future__ import annotations

OP_LDA = 0x02
OP_STA = 0x03
OP_ADD = 0x01
OP_CMP = 0x0D
OP_BEQ = 0x04
OP_JMP = 0x05
OP_CALL = 0x06
OP_RET = 0x07
OP_HALT = 0x0A

# Largest Fibonacci term to reach (sequence stops when fb == largest term <= FIB_LIMIT).
FIB_LIMIT = 250

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

    def call(self, target: str) -> int:
        pos = self._emit(OP_CALL, 0, 0)
        self._fixups.append((pos + 1, target))
        return pos

    def ret(self) -> int:
        return self._emit(OP_RET)

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
    if op in (OP_BEQ, OP_JMP, OP_CALL):
        return 3
    if op in (OP_HALT, OP_RET) or (op & 0x10) == 0x10:
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


def _emit_fib_loop(
    rb: RomBuilder,
    fa: int,
    fb: int,
    tmp: int,
    add_imm_pc: int,
    target: int,
) -> int:
    """Gi1 looped Fibonacci — JMP/BEQ outer (no CALL/RET).

    Gi1 ADD is R0+imm only; each step patches the ADD immediate byte in RAM
    (map_mode=1 program mirror) with the current ``fb`` before ``ADD #imm``.
    Returns PC of ``outer`` label for checkpoint tests.
    """
    rb.label("outer")
    outer_pc = rb.labels["outer"]
    rb.lda(fb)
    rb.cmp(target)
    rb.beq("halt")

    rb.lda(fb)
    rb.sta(tmp)
    rb.lda(fb)
    rb.sta(add_imm_pc)
    rb.lda(fa)
    rb.add(0)
    rb.sta(fb)
    rb.lda(tmp)
    rb.sta(fa)
    rb.jmp("outer")

    rb.label("halt")
    rb.halt()
    return outer_pc


def build_fib_to_limit_rom(
    limit: int = FIB_LIMIT,
) -> tuple[bytes, dict[int, int], int, int]:
    """
    ROM: JMP-loop Fibonacci in RAM until ``fb`` equals the largest term <= limit.

    RAM layout above ROM image: ``fa``, ``fb``, ``tmp``; ``add_imm_pc`` is the
    program offset of the ADD immediate byte (self-patched each outer iteration).

    Returns ``(rom, ram_init, target, outer_pc)`` — ``outer_pc`` is the loop-head
    PC for visit-count checkpoint tests.
    """
    global ADDR_FIB_A, ADDR_FIB_B

    target, _next = last_fib_leq(limit)

    probe = RomBuilder(0x0000)
    _emit_fib_loop(probe, 0xF0, 0xF1, 0xF2, 0xF3, target)
    probe_rom = probe.to_bytes()
    data_base = len(probe_rom)
    add_imm_pc = next(i + 1 for i in range(len(probe_rom) - 1) if probe_rom[i] == OP_ADD)

    fa = data_base
    fb = data_base + 1
    tmp = data_base + 2
    if tmp > 0xFF:
        raise ValueError(f"fib ROM {data_base} bytes — RAM layout exceeds addr8")

    rb = RomBuilder(0x0000)
    outer_pc = _emit_fib_loop(rb, fa, fb, tmp, add_imm_pc, target)
    rom = rb.to_bytes()
    assert len(rom) == data_base

    data_addrs = {fa, fb, tmp}
    fetches = _operand_fetch_pcs(rom)
    if fetches.intersection(data_addrs):
        raise ValueError("fib RAM aliases operand-fetch PCs — adjust layout")

    pairs = fib_pairs_to_limit(limit)
    checkpoints = [(outer_pc, a, b) for a, b in pairs]

    ADDR_FIB_A = fa
    ADDR_FIB_B = fb
    ram_init = {fa: 0, fb: 1}
    return rom, ram_init, target, outer_pc


def build_fib_250_rom() -> tuple[bytes, dict[int, int]]:
    """Fibonacci up to largest term <= FIB_LIMIT."""
    rom, ram, _, _ = build_fib_to_limit_rom(FIB_LIMIT)
    return rom, ram


def _emit_fib_recursive(
    rb: RomBuilder,
    depth_cell: int,
    scratch_cell: int,
    nsave_base: int,
    hold_base: int,
    result2: int,
    add_imm_pc: int,
    smc_sta_operand_pc: int,
    smc_lda_operand_pc: int,
    smc_sta_hold_patch_pc: int,
    smc_lda_hold_patch_pc: int,
) -> None:
    """``fib`` — R0 = n on entry/exit; depth-indexed frame via SMC STA/LDA."""
    rb.label("fib")
    rb.cmp(0)
    rb.beq("fib_base")
    rb.cmp(1)
    rb.beq("fib_base")

    rb.sta(scratch_cell)
    rb.lda(depth_cell)
    rb.add(nsave_base)
    rb.sta(smc_sta_operand_pc)
    rb.lda(scratch_cell)
    rb.sta(0)

    rb.lda(depth_cell)
    rb.add(1)
    rb.sta(depth_cell)

    rb.lda(scratch_cell)
    rb.add(0xFF)
    rb.call("fib")

    rb.sta(scratch_cell)
    rb.lda(depth_cell)
    rb.add(0xFF)
    rb.add(hold_base)
    rb.sta(smc_sta_hold_patch_pc)
    rb.lda(scratch_cell)
    rb.sta(0)

    rb.lda(depth_cell)
    rb.add(0xFF)
    rb.add(nsave_base)
    rb.sta(smc_lda_operand_pc)
    rb.lda(0)
    rb.add(0xFE)
    rb.call("fib")
    rb.sta(result2)

    rb.lda(depth_cell)
    rb.add(0xFF)
    rb.add(hold_base)
    rb.sta(smc_lda_hold_patch_pc)
    rb.lda(0)
    rb.sta(add_imm_pc)
    rb.lda(result2)
    rb.add(0)

    rb.sta(scratch_cell)
    rb.lda(depth_cell)
    rb.add(0xFF)
    rb.sta(depth_cell)
    rb.lda(scratch_cell)
    rb.ret()

    rb.label("fib_base")
    rb.ret()


def _fib_recursive_expected(n: int) -> int:
    if n <= 1:
        return n
    return _fib_recursive_expected(n - 1) + _fib_recursive_expected(n - 2)


def _find_smc_patches(rom: bytes) -> tuple[int, int, int, int, int]:
    """Return SMC operand PCs: add_imm, sta_n, lda_n, sta_hold, lda_hold."""
    add_imm_pc = 0
    sta_pcs: list[int] = []
    lda_pcs: list[int] = []
    for i in range(len(rom) - 1):
        op = rom[i]
        if op == OP_ADD and rom[i + 1] == 0:
            add_imm_pc = i + 1
        elif op == OP_STA and rom[i + 1] == 0:
            sta_pcs.append(i + 1)
        elif op == OP_LDA and rom[i + 1] == 0:
            lda_pcs.append(i + 1)
    if add_imm_pc == 0 or len(sta_pcs) < 2 or len(lda_pcs) < 2:
        raise ValueError("fib recursive ROM missing SMC patches")
    return add_imm_pc, sta_pcs[0], lda_pcs[0], sta_pcs[1], lda_pcs[1]


def build_fib_recursive_rom(n: int) -> tuple[bytes, dict[int, int], int]:
    """
    Recursive Fibonacci via CALL/RET.

    Returns ``(rom, ram_init, expected)`` where ``expected = fib(n)``.
    """
    from simulators.cyclesim.blocks.return_stack import RP_CELL, STACK_BASE

    expected = _fib_recursive_expected(n)

    probe = RomBuilder(0x0000)
    probe.label("main")
    probe.lda(0xF0)
    probe.call("fib")
    probe.sta(0xF1)
    probe.halt()
    _emit_fib_recursive(probe, 0xF2, 0xF3, 0xF4, 0xF8, 0xF5, 0x7D, 0x7E, 0x7F, 0x7A, 0x7B)
    probe_rom = probe.to_bytes()
    data_base = len(probe_rom)
    add_imm_pc, smc_sta_op, smc_lda_op, smc_sta_hold, smc_lda_hold = _find_smc_patches(probe_rom)

    n_arg = data_base
    result_out = data_base + 1
    result2 = data_base + 2
    depth_cell = data_base + 3
    scratch_cell = data_base + 4
    nsave_base = data_base + 5
    hold_base = nsave_base + n + 1
    if hold_base + n > 0xFF:
        raise ValueError(f"fib recursive n={n} out of range for addr8 frame slots")

    rb = RomBuilder(0x0000)
    rb.label("main")
    rb.lda(n_arg)
    rb.call("fib")
    rb.sta(result_out)
    rb.halt()
    _emit_fib_recursive(
        rb,
        depth_cell,
        scratch_cell,
        nsave_base,
        hold_base,
        result2,
        add_imm_pc,
        smc_sta_op,
        smc_lda_op,
        smc_sta_hold,
        smc_lda_hold,
    )
    rom = rb.to_bytes()
    assert len(rom) == data_base

    frame_addrs = set(range(nsave_base, nsave_base + n + 1)) | set(
        range(hold_base, hold_base + n + 1)
    )
    data_addrs = (
        {n_arg, result_out, result2, depth_cell, scratch_cell, RP_CELL, RP_CELL + 1}
        | frame_addrs
    )
    fetches = _operand_fetch_pcs(rom)
    if fetches.intersection(data_addrs):
        raise ValueError("fib recursive RAM aliases operand-fetch PCs — adjust layout")

    ram_init = {
        n_arg: n & 0xFF,
        depth_cell: 0,
        RP_CELL: STACK_BASE & 0xFF,
        RP_CELL + 1: (STACK_BASE >> 8) & 0xFF,
    }
    return rom, ram_init, expected
