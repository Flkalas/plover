#!/usr/bin/env python3
"""Cross-check microcode-spec.md expectations vs pack_control_store.py output."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hw.micro.reg_sel import reg_sel  # noqa: E402
from tools.pack_control_store import (  # noqa: E402
    ALU_ADD,
    ALU_CMP,
    ALU_NOP,
    ALU_SUB,
    CW_BEQ_CMP,
    CW_CMP_EXEC,
    CW_FLASH_BASE,
    OP_ADD,
    OP_BEQ,
    OP_CMP,
    OP_HALT,
    OP_JMP,
    OP_LDA,
    OP_LDIO,
    OP_STA,
    OP_STA16,
    OP_STIO,
    OP_MOV,
    build_all,
    cs_index,
    cw_hi,
    cw_lo,
    pack_cw,
    sequences,
)

# Normative bit fields from docs/hardware/microcode-spec.md §2
SPEC_BIT_MAP = {
    "alu_op": (7, 4),
    "reg_we": (3, 3),
    "y_oe": (2, 2),
    "mem_rd": (1, 1),
    "mem_wr": (0, 0),
}

# Documented CW rows in docs/hardware/microcode-spec.md §3 (packed opcodes)
SPEC_DOC_ROWS = {
    (OP_ADD, 0): {"alu_op": ALU_ADD, "reg_we": 0, "y_oe": 1, "mem_rd": 0, "mem_wr": 0},
    (OP_ADD, 1): {"alu_op": ALU_ADD, "reg_we": 0, "y_oe": 1, "mem_rd": 0, "mem_wr": 0},
    (OP_ADD, 2): {"alu_op": ALU_ADD, "reg_we": 1, "y_oe": 1, "mem_rd": 0, "mem_wr": 0},
    (OP_LDA, 0): {"alu_op": ALU_NOP, "reg_we": 0, "y_oe": 0, "mem_rd": 1, "mem_wr": 0},
    (OP_LDA, 1): {"alu_op": ALU_NOP, "reg_we": 1, "y_oe": 0, "mem_rd": 0, "mem_wr": 0},
    (OP_STA, 0): {"alu_op": ALU_NOP, "reg_we": 0, "y_oe": 1, "mem_rd": 0, "mem_wr": 0},
    (OP_STA, 1): {"alu_op": ALU_NOP, "reg_we": 0, "y_oe": 0, "mem_rd": 0, "mem_wr": 1},
    (OP_BEQ, 0): {"alu_op": ALU_SUB, "reg_we": 0, "y_oe": 0, "mem_rd": 0, "mem_wr": 0},
    (OP_BEQ, 1): {"alu_op": ALU_NOP, "reg_we": 0, "y_oe": 0, "mem_rd": 0, "mem_wr": 0},
    (OP_CMP, 0): {"alu_op": ALU_CMP, "reg_we": 0, "y_oe": 0, "mem_rd": 0, "mem_wr": 0},
    (OP_CMP, 1): {"alu_op": ALU_CMP, "reg_we": 0, "y_oe": 0, "mem_rd": 0, "mem_wr": 0},
    (OP_CMP, 2): {"alu_op": ALU_NOP, "reg_we": 0, "y_oe": 0, "mem_rd": 0, "mem_wr": 0},
    (OP_JMP, 0): {"alu_op": ALU_NOP, "reg_we": 0, "y_oe": 0, "mem_rd": 0, "mem_wr": 0},
    (OP_HALT, 0): {"alu_op": ALU_NOP, "reg_we": 0, "y_oe": 0, "mem_rd": 0, "mem_wr": 0},
    (OP_LDIO, 0): {"alu_op": ALU_NOP, "reg_we": 0, "y_oe": 0, "mem_rd": 1, "mem_wr": 0},
    (OP_LDIO, 1): {"alu_op": ALU_NOP, "reg_we": 1, "y_oe": 0, "mem_rd": 0, "mem_wr": 0},
    (OP_STIO, 0): {"alu_op": ALU_NOP, "reg_we": 0, "y_oe": 1, "mem_rd": 0, "mem_wr": 0},
    (OP_STIO, 1): {"alu_op": ALU_NOP, "reg_we": 0, "y_oe": 0, "mem_rd": 0, "mem_wr": 1},
    (OP_MOV, 0): {"alu_op": ALU_NOP, "reg_we": 0, "y_oe": 0, "mem_rd": 0, "mem_wr": 0},
    (OP_STA16, 0): {"alu_op": ALU_NOP, "reg_we": 0, "y_oe": 1, "mem_rd": 0, "mem_wr": 0},
    (OP_STA16, 1): {"alu_op": ALU_NOP, "reg_we": 0, "y_oe": 0, "mem_rd": 0, "mem_wr": 1},
}

# §3 draft rows — documented as TBD, intentionally absent from packer
SPEC_TBD_OPCODES = {0x06, 0x07}


def decode_cw(word: int) -> dict[str, int]:
    lo = cw_lo(word)
    return {
        "reg_sel": cw_hi(word),
        "alu_op": (lo >> 4) & 0xF,
        "reg_we": (lo >> 3) & 1,
        "y_oe": (lo >> 2) & 1,
        "mem_rd": (lo >> 1) & 1,
        "mem_wr": lo & 1,
    }


def pack_from_fields(op: int, ph: int, fields: dict[str, int]) -> int:
    return pack_cw(
        alu_op=fields["alu_op"],
        reg_we=fields["reg_we"],
        y_oe=fields["y_oe"],
        mem_rd=fields["mem_rd"],
        mem_wr=fields["mem_wr"],
        reg_sel_val=reg_sel(op, ph),
    )


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    # 1. pack_cw matches spec bit map (lo byte)
    probe = pack_cw(alu_op=0xA, reg_we=1, y_oe=1, mem_rd=1, mem_wr=1, reg_sel_val=0)
    if cw_lo(probe) != 0xAF:
        errors.append(f"pack_cw lo layout: expected 0xAF, got 0x{cw_lo(probe):02X}")

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
        want = pack_from_fields(op, ph, fields)
        if packed != want:
            errors.append(
                f"packer 0x{op:02X} ph{ph}: 0x{packed:04X} != spec 0x{want:04X}"
            )
        idx = cs_index(op, ph)
        if built[2 * idx] != cw_lo(want) or built[2 * idx + 1] != cw_hi(want):
            errors.append(
                f"store slot {idx}: lo=0x{built[2*idx]:02X} hi=0x{built[2*idx+1]:02X} "
                f"!= 0x{cw_lo(want):02X}/0x{cw_hi(want):02X}"
            )

    # 5. Flash base
    if CW_FLASH_BASE != 0x4000:
        errors.append(f"CW_FLASH_BASE = 0x{CW_FLASH_BASE:X}, spec says $4000")

    if CW_CMP_EXEC != 0xB0:
        errors.append(f"CW_CMP_EXEC = 0x{CW_CMP_EXEC:02X}, expected 0xB0")
    if CW_BEQ_CMP != 0x20:
        errors.append(f"CW_BEQ_CMP = 0x{CW_BEQ_CMP:02X}, expected 0x20 (SUB, Y_OE=0)")

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
    print("Control Store v1.0 verification (10b CW)")
    print("=" * 60)
    print(f"Flash base: 0x{CW_FLASH_BASE:04X}  store size: {len(built)} bytes")
    print(f"cs_index: ((opcode & 0xF) << 2) | (phase & 3)")
    print()
    print("Non-zero entries (packer):")
    for idx in range(0, len(built) // 2):
        lo, hi = built[2 * idx], built[2 * idx + 1]
        if lo or hi:
            op = (idx >> 2) & 0xF
            ph = idx & 3
            word = lo | (hi << 8)
            dec = decode_cw(word)
            print(
                f"  idx={idx:4d} Flash=0x{CW_FLASH_BASE + 2*idx:04X} "
                f"op=0x{op:X} ph={ph} lo=0x{lo:02X} hi=0x{hi:02X} "
                f"REG_SEL={dec['reg_sel']} ALU={dec['alu_op']}"
            )

    print()
    print("Documented packed rows (microcode-spec.md §3):")
    for (op, ph), fields in sorted(SPEC_DOC_ROWS.items()):
        idx = cs_index(op, ph)
        word = built[2 * idx] | (built[2 * idx + 1] << 8)
        dec = decode_cw(word)
        match = {k: dec[k] for k in fields} == fields and dec["reg_sel"] == reg_sel(op, ph)
        print(f"  0x{op:02X} ph{ph} idx={idx} match={match} {dec}")
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
