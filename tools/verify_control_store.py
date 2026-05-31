#!/usr/bin/env python3
"""Cross-check microcode-spec.md expectations vs pack_control_store.py output."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.pack_control_store import (  # noqa: E402
    ALU_ADD,
    ALU_NOP,
    ALU_SUB,
    CW_FLASH_BASE,
    OP_ADD,
    OP_BEQ,
    OP_HALT,
    OP_JMP,
    OP_LDA,
    OP_STA,
    build_all,
    cs_index,
    pack_cw,
    sequences,
)

# Normative bit fields from docs/microcode-spec.md §2
SPEC_BIT_MAP = {
    "alu_op": (7, 4),
    "reg_we": (3, 3),
    "y_oe": (2, 2),
    "mem_rd": (1, 1),
    "mem_wr": (0, 0),
}

# Documented CW rows in docs/microcode-spec.md §3 (packed opcodes)
SPEC_DOC_ROWS = {
    (OP_ADD, 0): {"alu_op": ALU_ADD, "reg_we": 0, "y_oe": 1, "mem_rd": 0, "mem_wr": 0},
    (OP_ADD, 1): {"alu_op": ALU_ADD, "reg_we": 0, "y_oe": 1, "mem_rd": 0, "mem_wr": 0},
    (OP_ADD, 2): {"alu_op": ALU_ADD, "reg_we": 1, "y_oe": 1, "mem_rd": 0, "mem_wr": 0},
    (OP_LDA, 0): {"alu_op": ALU_NOP, "reg_we": 0, "y_oe": 0, "mem_rd": 1, "mem_wr": 0},
    (OP_LDA, 1): {"alu_op": ALU_NOP, "reg_we": 1, "y_oe": 0, "mem_rd": 0, "mem_wr": 0},
    (OP_STA, 0): {"alu_op": ALU_NOP, "reg_we": 0, "y_oe": 1, "mem_rd": 0, "mem_wr": 0},
    (OP_STA, 1): {"alu_op": ALU_NOP, "reg_we": 0, "y_oe": 0, "mem_rd": 0, "mem_wr": 1},
    (OP_BEQ, 0): {"alu_op": ALU_SUB, "reg_we": 0, "y_oe": 1, "mem_rd": 0, "mem_wr": 0},
    (OP_BEQ, 1): {"alu_op": ALU_NOP, "reg_we": 0, "y_oe": 0, "mem_rd": 0, "mem_wr": 0},
    (OP_JMP, 0): {"alu_op": ALU_NOP, "reg_we": 0, "y_oe": 0, "mem_rd": 0, "mem_wr": 0},
    (OP_HALT, 0): {"alu_op": ALU_NOP, "reg_we": 0, "y_oe": 0, "mem_rd": 0, "mem_wr": 0},
}

# §3 draft rows — documented as TBD, intentionally absent from packer
SPEC_TBD_OPCODES = {0x06, 0x07, 0x08, 0x09}


def decode_cw(raw: int) -> dict[str, int]:
    return {
        "alu_op": (raw >> 4) & 0xF,
        "reg_we": (raw >> 3) & 1,
        "y_oe": (raw >> 2) & 1,
        "mem_rd": (raw >> 1) & 1,
        "mem_wr": raw & 1,
    }


def pack_from_fields(fields: dict[str, int]) -> int:
    return pack_cw(
        alu_op=fields["alu_op"],
        reg_we=fields["reg_we"],
        y_oe=fields["y_oe"],
        mem_rd=fields["mem_rd"],
        mem_wr=fields["mem_wr"],
    )


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    # 1. pack_cw matches spec bit map
    probe = pack_cw(alu_op=0xA, reg_we=1, y_oe=1, mem_rd=1, mem_wr=1)
    if probe != 0xAF:
        errors.append(f"pack_cw bit layout: expected 0xAF, got 0x{probe:02X}")

    # 2. cs_index matches rom-architecture {opcode[3:0], phase[1:0]}
    for op, ph, want in [(0x01, 0, 4), (0x0A, 0, 40), (0x03, 1, 13)]:
        got = cs_index(op, ph)
        if got != want:
            errors.append(f"cs_index(0x{op:02X},{ph}) = {got}, expected {want}")

    # 3. build_all vs cw.hex on disk
    built = build_all()
    hex_path = ROOT / "hw" / "fixtures" / "control" / "cw.hex"
    if hex_path.exists():
        hex_words = [int(line.strip(), 16) for line in hex_path.read_text().splitlines() if line.strip()]
        if len(hex_words) != len(built):
            errors.append(f"cw.hex length {len(hex_words)} != store {len(built)}")
        for i, (a, b) in enumerate(zip(built, hex_words)):
            if a != b:
                errors.append(f"cw.hex[{i}]: file=0x{b:02X} packer=0x{a:02X}")
                break
    else:
        warnings.append("cw.hex missing — run pack_control_store.py --build-fixtures")

    # 4. Packer sequences vs documented rows
    seq = sequences()
    packed_ops = set(seq.keys())
    for key, fields in SPEC_DOC_ROWS.items():
        op, ph = key
        if op not in seq or ph >= len(seq[op]):
            errors.append(f"packer missing sequence for documented op 0x{op:02X} phase {ph}")
            continue
        packed = seq[op][ph]
        want = pack_from_fields(fields)
        if packed != want:
            errors.append(f"packer 0x{op:02X} ph{ph}: 0x{packed:02X} != spec 0x{want:02X}")
        idx = cs_index(op, ph)
        if built[idx] != want:
            errors.append(f"store[{idx}] = 0x{built[idx]:02X}, spec wants 0x{want:02X}")

    # 5. Flash base
    if CW_FLASH_BASE != 0x4000:
        errors.append(f"CW_FLASH_BASE = 0x{CW_FLASH_BASE:X}, spec says $4000")

    # 6. Packer must cover every packed spec row; no extra undocumented rows
    documented_keys = set(SPEC_DOC_ROWS.keys())
    packed_keys: set[tuple[int, int]] = set()
    for op, phases in seq.items():
        for ph, _cw in enumerate(phases):
            packed_keys.add((op, ph))
    for key in documented_keys - packed_keys:
        errors.append(f"packer missing documented row {key}")
    for key in packed_keys - documented_keys:
        errors.append(f"packer row {key} not in microcode-spec.md §3 packed tables")

    # 7. TBD opcodes (§3 draft) must stay out of packer until implemented
    for op in SPEC_TBD_OPCODES:
        if op in packed_ops:
            errors.append(f"TBD opcode 0x{op:02X} must not be packed yet")
        else:
            warnings.append(f"opcode 0x{op:02X} documented as TBD in spec §3 (not in cw.hex)")

    # 8. Non-zero store summary
    print("Control Store v0.1 verification")
    print("=" * 60)
    print(f"Flash base: 0x{CW_FLASH_BASE:04X}  store size: {len(built)} bytes")
    print(f"cs_index: ((opcode & 0xF) << 2) | (phase & 3)")
    print()
    print("Non-zero entries (packer):")
    for i, w in enumerate(built):
        if w:
            op = (i >> 2) & 0xF
            ph = i & 3
            dec = decode_cw(w)
            print(
                f"  idx={i:4d} Flash=0x{CW_FLASH_BASE + i:04X} "
                f"op_nib=0x{op:X} ph={ph} raw=0x{w:02X} "
                f"ALU={dec['alu_op']} REG_WE={dec['reg_we']} Y_OE={dec['y_oe']} "
                f"MEM_RD={dec['mem_rd']} MEM_WR={dec['mem_wr']}"
            )

    print()
    print("Documented packed rows (microcode-spec.md §3):")
    for (op, ph), fields in sorted(SPEC_DOC_ROWS.items()):
        idx = cs_index(op, ph)
        raw = built[idx]
        dec = decode_cw(raw)
        match = dec == fields
        print(
            f"  0x{op:02X} ph{ph} idx={idx} match={match} "
            f"raw=0x{raw:02X} {dec}"
        )
        if not match:
            errors.append(f"decoded store != spec for 0x{op:02X} ph{ph}")

    print()
    if warnings:
        print(f"Warnings ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")
        print()

    if errors:
        print(f"FAILED ({len(errors)} errors):")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("PASS: spec §2 bit map, §3 packed rows, cs_index, Flash $4000, cw.hex")
    if warnings:
        print(f"({len(warnings)} coverage gaps - see warnings)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
