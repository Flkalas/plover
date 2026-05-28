#!/usr/bin/env python3
"""Assemble Plover microcode source to 16-bit control words."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ALU_OPS = {
    "NOP": 0, "ADD": 1, "SUB": 2, "AND": 3, "OR": 4, "XOR": 5,
    "NOT": 6, "PASS_A": 7, "PASS_B": 8, "INC": 9, "DEC": 10, "CMP": 11,
}

BUS_OPS = {
    "IDLE": 0, "ALU_TO_REG": 1, "REG_TO_ALU_B": 2,
    "MEM_READ": 3, "MEM_WRITE": 4, "IMM8_LO": 5,
}

BRANCH_OPS = {
    "INC": 0, "HOLD": 1, "JMP": 2, "BEQ": 3, "BNE": 4, "HALT": 5, "INC2": 6,
}

REG_NUM = re.compile(r"R([0-6])", re.IGNORECASE)


def reg_num(s: str) -> int:
    m = REG_NUM.search(s)
    if not m:
        raise ValueError(f"expected register in {s!r}")
    return int(m.group(1))


def reg_ctl(idx: int, write: bool) -> int:
    return ((idx & 7) << 1) | (1 if write else 0)


def parse_line(line: str) -> int | None:
    line = line.split(";", 1)[0].strip()
    if not line or line.startswith("@"):
        return None

    alu_sel = 0
    reg_field = 0
    bus_ctl = 0
    branch = 0

    for part in line.split("|"):
        part = part.strip()
        if not part:
            continue
        key, _, val = part.partition(" ")
        key = key.lower()
        val = val.strip().upper()

        if key == "alu":
            alu_sel = ALU_OPS[val]
        elif key == "bus":
            bus_ctl = BUS_OPS[val]
        elif key == "branch":
            branch = BRANCH_OPS[val]
        elif key == "reg":
            if "<=ALU" in val or "<= ALU" in val.replace(" ", ""):
                r = reg_num(val)
                reg_field = reg_ctl(r, True)
                if bus_ctl == 0:
                    bus_ctl = BUS_OPS["ALU_TO_REG"]
            elif "=>ALU" in val or "=> ALU" in val.replace(" ", ""):
                r = reg_num(val)
                reg_field = reg_ctl(r, False)
            elif "<=" in val:
                dst_s, src_s = val.split("<=", 1)
                dst, src = reg_num(dst_s), reg_num(src_s)
                if dst != src:
                    raise ValueError(
                        "single reg field: use two lines for cross-register move"
                    )
                reg_field = reg_ctl(dst, True)
            else:
                raise ValueError(f"bad reg: {val}")
        else:
            raise ValueError(f"unknown field: {key}")

    return (alu_sel << 12) | (reg_field << 8) | (bus_ctl << 4) | branch


def assemble(source: str) -> list[tuple[int, int]]:
    addr = 0
    out: list[tuple[int, int]] = []
    for line in source.splitlines():
        m = re.match(r"@([0-9a-fA-F]+)", line.strip())
        if m:
            addr = int(m.group(1), 16)
            continue
        cw = parse_line(line)
        if cw is None:
            continue
        out.append((addr, cw))
        addr += 1
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Plover microassembler")
    ap.add_argument("input", type=Path)
    ap.add_argument("-o", "--out-dir", type=Path, default=Path("sim"))
    args = ap.parse_args()

    words = assemble(args.input.read_text(encoding="utf-8"))
    if not words:
        print("no instructions", file=sys.stderr)
        return 1

    max_addr = max(a for a, _ in words)
    lo, hi = [0] * (max_addr + 1), [0] * (max_addr + 1)
    for addr, cw in words:
        lo[addr], hi[addr] = cw & 0xFF, (cw >> 8) & 0xFF

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "rom_low.hex").write_text(
        "\n".join(f"{b:02x}" for b in lo) + "\n", encoding="utf-8"
    )
    (args.out_dir / "rom_high.hex").write_text(
        "\n".join(f"{b:02x}" for b in hi) + "\n", encoding="utf-8"
    )

    for addr, cw in words:
        print(f"@{addr:04x}  {cw:04x}")
    print(f"wrote {len(lo)} words to {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
