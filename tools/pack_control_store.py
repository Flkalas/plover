#!/usr/bin/env python3
"""Pack v0.1 control store: {opcode, phase} -> 8-bit CW for SST39SF010A."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CW_FLASH_BASE = 0x4000
STORE_SIZE = 2048

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

ALU_NOP = 0
ALU_ADD = 1
ALU_SUB = 2


def pack_cw(
    alu_op: int = 0,
    reg_we: int = 0,
    y_oe: int = 0,
    mem_rd: int = 0,
    mem_wr: int = 0,
) -> int:
    return (
        ((alu_op & 0xF) << 4)
        | ((reg_we & 1) << 3)
        | ((y_oe & 1) << 2)
        | ((mem_rd & 1) << 1)
        | (mem_wr & 1)
    )


def cs_index(opcode: int, phase: int) -> int:
    return ((opcode & 0xF) << 2) | (phase & 3)


def pack_store(words: dict[tuple[int, int], int]) -> list[int]:
    store = [0] * STORE_SIZE
    for (op, ph), cw in words.items():
        store[cs_index(op, ph)] = cw & 0xFF
    return store


def sequences() -> dict[int, list[int]]:
    return {
        OP_ADD: [
            pack_cw(alu_op=ALU_ADD, y_oe=1),
            pack_cw(alu_op=ALU_ADD, y_oe=1),
            pack_cw(alu_op=ALU_ADD, reg_we=1, y_oe=1),
        ],
        OP_LDA: [
            pack_cw(alu_op=ALU_NOP, mem_rd=1),
            pack_cw(alu_op=ALU_NOP, reg_we=1),
        ],
        OP_STA: [
            pack_cw(alu_op=ALU_NOP, y_oe=1),
            pack_cw(alu_op=ALU_NOP, mem_wr=1),
        ],
        OP_BEQ: [
            pack_cw(alu_op=ALU_SUB, y_oe=1),
            pack_cw(alu_op=ALU_NOP),
        ],
        OP_JMP: [pack_cw(alu_op=ALU_NOP)],
        OP_HALT: [pack_cw(alu_op=ALU_NOP)],
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
    # Flash image slice @ CW_FLASH_BASE (sparse tail only for sim)
    flash_path = out_dir / "nor_cw_region.hex"
    lines = ["00"] * CW_FLASH_BASE
    lines.extend(f"{w:02X}" for w in words)
    flash_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Pack v0.1 8-bit control store")
    ap.add_argument("--out", type=Path, default=ROOT / "hw" / "fixtures" / "control")
    ap.add_argument("--build-fixtures", action="store_true")
    args = ap.parse_args()

    words = build_all()
    if args.build_fixtures:
        write_hex(words, args.out)
        print(f"wrote {len(words)} CW entries -> {args.out}")
        return

    for i, w in enumerate(words[:32]):
        if w:
            print(f"  [{i:04x}] 0x{w:02X}")
    print(f"non-zero entries: {sum(1 for w in words if w)}")


if __name__ == "__main__":
    main()
