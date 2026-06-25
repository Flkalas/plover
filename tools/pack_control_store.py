#!/usr/bin/env python3
"""Pack v1.0 control store: {opcode, phase} -> 10-bit CW for SST39SF010A."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hw.micro.reg_sel import reg_sel  # noqa: E402

CW_FLASH_BASE = 0x4000
STORE_SLOTS = 2048

CW16_REG_WSEL_SHIFT = 14
CW16_Y_MUX_SHIFT = 13
CW16_LGC_SHIFT = 9
CW16_CIN_SHIFT = 8
CW16_B_SEL_SHIFT = 7
CW16_B_CONST_SEL_SHIFT = 6
CW16_FLAGS_ONLY_SHIFT = 5
CW16_REG_WE_SHIFT = 4
CW16_Y_OE_SHIFT = 3
CW16_MEM_RD_SHIFT = 2
CW16_MEM_WR_SHIFT = 1

OP_ADD = 0x01
OP_LDA = 0x02
OP_STA = 0x03
OP_BEQ = 0x04
OP_JMP = 0x05
OP_CALL = 0x06
OP_RET = 0x07
OP_LDIO = 0x08
OP_STIO = 0x09
OP_HALT = 0x0A
OP_MOV = 0x0C  # deprecated — reserved on breadboard; use TFR opcodes
OP_CMP = 0x0D
OP_STA16 = 0x0F

OP_TFR01 = 0x10
OP_TFR02 = 0x11
OP_TFR10 = 0x12
OP_TFR12 = 0x13
OP_TFR20 = 0x14
OP_TFR21 = 0x15

# Normative v1.0 FSM-only: opcode → template, phases, internal w_sel / xfer routing
FSM_OPCODE_TABLE: dict[int, dict] = {
    OP_ADD: {"template": "ALU_REG", "phases": 3, "w_sel": 2},
    OP_LDA: {"template": "MEM_LD", "phases": 2, "w_sel": 0},
    OP_STA: {"template": "MEM_ST", "phases": 2},
    OP_BEQ: {"template": "BEQ", "phases": 2, "pc_load": "FLG_Z"},
    OP_JMP: {"template": "JMP", "phases": 1, "pc_load": 1},
    OP_CMP: {"template": "ALU_REG", "phases": 3, "w_sel": 0},
    OP_HALT: {"template": "HALT", "phases": 1},
    OP_LDIO: {"template": "MEM_LD", "phases": 2, "w_sel": 0},
    OP_STIO: {"template": "MEM_ST", "phases": 2},
    OP_STA16: {"template": "MEM_ST", "phases": 2},
    OP_TFR01: {"template": "XFER", "phases": 1, "dst": 0, "src": 1},
    OP_TFR02: {"template": "XFER", "phases": 1, "dst": 0, "src": 2},
    OP_TFR10: {"template": "XFER", "phases": 1, "dst": 1, "src": 0},
    OP_TFR12: {"template": "XFER", "phases": 1, "dst": 1, "src": 2},
    OP_TFR20: {"template": "XFER", "phases": 1, "dst": 2, "src": 0},
    OP_TFR21: {"template": "XFER", "phases": 1, "dst": 2, "src": 1},
}

ALU_NOP = 0
ALU_ADD = 1
ALU_SUB = 2
ALU_CMP = 11


def pack_cw(
    alu_op: int = 0,
    reg_we: int = 0,
    y_oe: int = 0,
    mem_rd: int = 0,
    mem_wr: int = 0,
    reg_sel_val: int = 0,
) -> int:
    """10-bit CW: B9-B8 REG_SEL, B7-B0 legacy control."""
    lo = (
        ((alu_op & 0xF) << 4)
        | ((reg_we & 1) << 3)
        | ((y_oe & 1) << 2)
        | ((mem_rd & 1) << 1)
        | (mem_wr & 1)
    )
    hi = reg_sel_val & 3
    return lo | (hi << 8)


def cw_lo(word: int) -> int:
    return word & 0xFF


def cw_hi(word: int) -> int:
    return (word >> 8) & 0xFF


# Compare / flag-only execute — ALU runs, result must not drive the data bus.
CW_CMP_EXEC = pack_cw(alu_op=ALU_CMP, y_oe=0)  # lo 0xB0
CW_BEQ_CMP = pack_cw(alu_op=ALU_SUB, y_oe=0)  # lo 0x20


def cs_index(opcode: int, phase: int) -> int:
    """Archived idx4: (opcode[3:0]<<2)|phase — prototype-flash-cw only."""
    return ((opcode & 0xF) << 2) | (phase & 3)


def cs_index5(opcode: int, phase: int) -> int:
    """Normative v1.0 CPLD FSM key: (opcode[4:0]<<2)|phase — 128 logical slots."""
    return ((opcode & 0x1F) << 2) | (phase & 3)


def cs_index8(opcode: int, phase: int) -> int:
    return ((opcode & 0xFF) << 2) | (phase & 3)


def pack_cw16(
    *,
    reg_wsel: int = 0,
    y_mux_sel: int = 0,
    lgc: int = 0,
    cin: int = 0,
    b_sel: int = 0,
    b_const_sel: int = 0,
    flags_only: int = 0,
    reg_we: int = 0,
    y_oe: int = 0,
    mem_rd: int = 0,
    mem_wr: int = 0,
) -> int:
    """16-bit cw_direct control word (P1 bypass / research H2)."""
    return (
        ((reg_wsel & 3) << CW16_REG_WSEL_SHIFT)
        | ((y_mux_sel & 1) << CW16_Y_MUX_SHIFT)
        | ((lgc & 0xF) << CW16_LGC_SHIFT)
        | ((cin & 1) << CW16_CIN_SHIFT)
        | ((b_sel & 1) << CW16_B_SEL_SHIFT)
        | ((b_const_sel & 1) << CW16_B_CONST_SEL_SHIFT)
        | ((flags_only & 1) << CW16_FLAGS_ONLY_SHIFT)
        | ((reg_we & 1) << CW16_REG_WE_SHIFT)
        | ((y_oe & 1) << CW16_Y_OE_SHIFT)
        | ((mem_rd & 1) << CW16_MEM_RD_SHIFT)
        | ((mem_wr & 1) << CW16_MEM_WR_SHIFT)
    )


def pack_cw16_store(words: dict[tuple[int, int], int], *, index8: bool = False) -> list[int]:
    store = [0] * (STORE_SLOTS * 2)
    for (op, ph), cw in words.items():
        idx = cs_index8(op, ph) if index8 else cs_index(op, ph)
        store[2 * idx] = cw & 0xFF
        store[2 * idx + 1] = (cw >> 8) & 0xFF
    return store


def fsm_opcode_table() -> dict[int, dict]:
    return dict(FSM_OPCODE_TABLE)


def build_hybrid_all() -> list[int]:
    """Empty Flash $4000 image — FSM-only control (no CW rows)."""
    return [0] * (STORE_SLOTS * 2)


def pack_store(words: dict[tuple[int, int], int]) -> list[int]:
    """Flat byte image: 2 bytes per slot (lo @ 2*idx, hi @ 2*idx+1)."""
    store = [0] * (STORE_SLOTS * 2)
    for (op, ph), cw in words.items():
        idx = cs_index(op, ph)
        store[2 * idx] = cw_lo(cw)
        store[2 * idx + 1] = cw_hi(cw)
    return store


def _cw(
    op: int,
    ph: int,
    *,
    alu_op: int = 0,
    reg_we: int = 0,
    y_oe: int = 0,
    mem_rd: int = 0,
    mem_wr: int = 0,
) -> int:
    return pack_cw(
        alu_op=alu_op,
        reg_we=reg_we,
        y_oe=y_oe,
        mem_rd=mem_rd,
        mem_wr=mem_wr,
        reg_sel_val=reg_sel(op, ph),
    )


def sequences() -> dict[int, list[int]]:
    return {
        OP_ADD: [
            _cw(OP_ADD, 0, alu_op=ALU_ADD, y_oe=1),
            _cw(OP_ADD, 1, alu_op=ALU_ADD, y_oe=1),
            _cw(OP_ADD, 2, alu_op=ALU_ADD, reg_we=1, y_oe=1),
        ],
        OP_LDA: [
            _cw(OP_LDA, 0, alu_op=ALU_NOP, mem_rd=1),
            _cw(OP_LDA, 1, alu_op=ALU_NOP, reg_we=1),
        ],
        OP_STA: [
            _cw(OP_STA, 0, alu_op=ALU_NOP, y_oe=1),
            _cw(OP_STA, 1, alu_op=ALU_NOP, mem_wr=1),
        ],
        OP_BEQ: [
            _cw(OP_BEQ, 0, alu_op=ALU_SUB, y_oe=0),
            _cw(OP_BEQ, 1, alu_op=ALU_NOP),
        ],
        OP_CMP: [
            _cw(OP_CMP, 0, alu_op=ALU_CMP, y_oe=0),
            _cw(OP_CMP, 1, alu_op=ALU_CMP, y_oe=0),
            _cw(OP_CMP, 2, alu_op=ALU_NOP),
        ],
        OP_JMP: [_cw(OP_JMP, 0, alu_op=ALU_NOP)],
        OP_HALT: [_cw(OP_HALT, 0, alu_op=ALU_NOP)],
        OP_LDIO: [
            _cw(OP_LDIO, 0, alu_op=ALU_NOP, mem_rd=1),
            _cw(OP_LDIO, 1, alu_op=ALU_NOP, reg_we=1),
        ],
        OP_STIO: [
            _cw(OP_STIO, 0, alu_op=ALU_NOP, y_oe=1),
            _cw(OP_STIO, 1, alu_op=ALU_NOP, mem_wr=1),
        ],
        OP_MOV: [_cw(OP_MOV, 0, alu_op=ALU_NOP)],
        OP_STA16: [
            _cw(OP_STA16, 0, alu_op=ALU_NOP, y_oe=1),
            _cw(OP_STA16, 1, alu_op=ALU_NOP, mem_wr=1),
        ],
    }


def build_all() -> list[int]:
    mapping: dict[tuple[int, int], int] = {}
    for op, phases in sequences().items():
        for ph, cw in enumerate(phases):
            mapping[(op, ph)] = cw
    return pack_store(mapping)


def write_hex(words: list[int], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    cw_path = out_dir / "cw.hex"
    cw_path.write_text("\n".join(f"{w:02X}" for w in words) + "\n", encoding="utf-8")
    flash_path = out_dir / "nor_cw_region.hex"
    lines = ["00"] * CW_FLASH_BASE
    lines.extend(f"{w:02X}" for w in words)
    flash_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Pack control store (prototype 10b CW archive or FSM-only stub)"
    )
    ap.add_argument("--out", type=Path, default=ROOT / "hw" / "fixtures" / "control")
    ap.add_argument("--build-fixtures", action="store_true")
    ap.add_argument(
        "--hybrid",
        action="store_true",
        help="Write empty FSM-only $4000 stub (normative v1.0 has no Flash CW)",
    )
    args = ap.parse_args()

    if args.hybrid:
        words = build_hybrid_all()
        if args.build_fixtures:
            write_hex(words, args.out)
            print(f"wrote empty FSM-only stub ({len(words)} bytes) -> {args.out}")
            return
        print("FSM-only v1.0: no Flash param rows (use verify_control_store.py --v1.0)")
        return

    words = build_all()
    if args.build_fixtures:
        write_hex(words, args.out)
        print(f"wrote {len(words)} CW bytes ({STORE_SLOTS} slots × 2) -> {args.out}")
        return

    for i in range(0, min(len(words), 64), 2):
        if words[i] or words[i + 1]:
            slot = i // 2
            print(f"  slot={slot:04x} lo=0x{words[i]:02X} hi=0x{words[i+1]:02X}")
    print(f"non-zero byte pairs: {sum(1 for i in range(0, len(words), 2) if words[i] or words[i+1])}")


if __name__ == "__main__":
    main()
