#!/usr/bin/env python3
"""Pack v0.2 16-bit control words into rom_low.hex / rom_high.hex / rom_words.hex."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from alu8_cases import CASES  # noqa: E402

BUS_LOCAL = 0
BUS_IMM = 3

# ctrl bit map: 5=br_msb, 4=br_lsb, 3=FLG_WE, 2=INC, 1=HALT, 0=IRQ
BR_NORMAL = 0
BR_BEQ = 1
BR_JMP = 2
BR_BNE = 3


def pack_local_ctrl(
    *,
    flg_we: bool = False,
    inc: bool = True,
    branch: str | int = "normal",
    halt: bool = False,
    irq_mask: bool = False,
) -> int:
    if isinstance(branch, str):
        br = {"normal": BR_NORMAL, "beq": BR_BEQ, "jmp": BR_JMP, "bne": BR_BNE}[branch.lower()]
    else:
        br = int(branch) & 0x3
    return (
        ((br >> 1) & 1) << 5
        | (br & 1) << 4
        | (1 if flg_we else 0) << 3
        | (1 if inc else 0) << 2
        | (1 if halt else 0) << 1
        | (1 if irq_mask else 0)
    )


def cw_cmp_flg(src: int, dst: int) -> int:
    return pack_cw(op_id("CMP"), src, dst, BUS_LOCAL, pack_local_ctrl(flg_we=True, inc=True))


def cw_beq(*, inc: bool = False) -> int:
    return pack_cw(op_id("PASS_B"), 0, 0, BUS_LOCAL, pack_local_ctrl(branch="beq", inc=inc))


def cw_bne(*, inc: bool = False) -> int:
    return pack_cw(op_id("PASS_B"), 0, 0, BUS_LOCAL, pack_local_ctrl(branch="bne", inc=inc))


def cw_jmp() -> int:
    return pack_cw(op_id("PASS_B"), 0, 0, BUS_LOCAL, pack_local_ctrl(branch="jmp", inc=False))


def cw_local_nop(*, inc: bool = True) -> int:
    return pack_cw(op_id("PASS_B"), 0, 0, BUS_LOCAL, pack_local_ctrl(inc=inc))


def cw_dec(reg: int) -> int:
    return pack_cw(op_id("DEC"), reg, reg, BUS_LOCAL, pack_local_ctrl(inc=True))


def build_branch_slot_program() -> list[int]:
    """Preset R0=R1=3, CMP+FLG, DEC R1×3, BEQ -> PC=3."""
    words = [cw_inc(0)] * 3 + [cw_inc(1)] * 3
    words += [cw_cmp_flg(0, 1)]
    words += [cw_dec(1)] * 3
    words += [cw_beq(), cw_local_nop(), cw_local_nop()]
    return words


def build_p3_clock_demo() -> list[int]:
    """INC R2 ×2 + ADD R0→R2 (R0=0) → R2=2 under manual 161 PC stepping."""
    return [cw_inc(2), cw_inc(2), cw_add(0, 2)]


def pack_cw(
    alu_op: int,
    src: int,
    dst: int,
    bus_en: int = 0,
    ctrl: int = 0,
) -> int:
    """CW[15:0] = { alu_op, src, dst, bus_en, ctrl } per microcode-spec v0.2."""
    return (
        ((alu_op & 0xF) << 12)
        | ((src & 0x3) << 10)
        | ((dst & 0x3) << 8)
        | ((bus_en & 0x3) << 6)
        | (ctrl & 0x3F)
    )


def op_id(name: str) -> int:
    return next(i for i, (n, *_rest) in enumerate(CASES) if n == name)


def cw_inc(reg: int) -> int:
    return pack_cw(op_id("INC"), reg, reg, BUS_LOCAL, pack_local_ctrl(inc=True))


def cw_add(src: int, dst: int) -> int:
    return pack_cw(op_id("ADD"), src, dst, BUS_LOCAL, pack_local_ctrl(inc=True))


def cw_pass_b(src: int, dst: int, bus_en: int = BUS_LOCAL, ctrl: int = 0) -> int:
    return pack_cw(op_id("PASS_B"), src, dst, bus_en, ctrl)


def pack_imm_literal(literal: int) -> int:
    """IMM CW: bus_en=11, ADD src=R2 (A=0) + B=IMM; CP→R2 via dst_eff override."""
    imm = literal & 0xFF
    dst = (imm >> 6) & 0x3
    ctrl = imm & 0x3F
    return pack_cw(op_id("ADD"), 2, dst, BUS_IMM, ctrl)


def write_hex(words: list[int], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    lo = [w & 0xFF for w in words]
    hi = [(w >> 8) & 0xFF for w in words]
    (out_dir / "rom_low.hex").write_text(
        "\n".join(f"{b:02x}" for b in lo) + "\n", encoding="utf-8"
    )
    (out_dir / "rom_high.hex").write_text(
        "\n".join(f"{b:02x}" for b in hi) + "\n", encoding="utf-8"
    )
    (out_dir / "rom_words.hex").write_text(
        "\n".join(f"{w:04x}" for w in words) + "\n", encoding="utf-8"
    )


def load_words_file(path: Path) -> list[int]:
    words: list[int] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split(";", 1)[0].strip()
        if not line:
            continue
        words.append(int(line, 16))
    return words


def build_fixtures() -> None:
    fixtures = ROOT / "hw" / "fixtures" / "rom"
    write_hex([cw_add(0, 2)], fixtures / "single_add")
    write_hex(
        [
            cw_inc(0),
            cw_inc(2),
            cw_inc(2),
            cw_add(0, 2),
        ],
        fixtures / "clock_add_demo",
    )
    write_hex([pack_imm_literal(0xA5)], fixtures / "imm_a5")
    rmw: list[int] = [cw_inc(0)] * 0x12 + [cw_inc(2)] * 0x34 + [cw_add(0, 2)]
    write_hex(rmw, fixtures / "rmw_add")
    # branch_slot: CMP R0 vs R1 + FLG_WE, then BEQ (target in R1:R0 preset externally)
    write_hex(
        build_branch_slot_program(),
        fixtures / "branch_slot",
    )
    write_hex(build_p3_clock_demo(), fixtures / "p3_clock_add")
    print(f"wrote fixtures under {fixtures}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Pack v0.2 CW into ROM hex files")
    ap.add_argument("words", nargs="*", help="16-bit hex words e.g. 1900")
    ap.add_argument("-f", "--file", type=Path, help="one hex word per line")
    ap.add_argument("-o", "--out-dir", type=Path, default=Path("hw/fixtures/rom/out"))
    ap.add_argument("--build-fixtures", action="store_true", help="Write standard hw/fixtures/rom/*")
    ap.add_argument(
        "--demo",
        choices=("single_add", "clock_add_demo", "imm_a5"),
        help="Pack a named fixture program",
    )
    args = ap.parse_args()

    if args.build_fixtures:
        build_fixtures()
        return 0

    if args.demo:
        src = ROOT / "hw" / "fixtures" / "rom" / args.demo / "rom_words.hex"
        if not src.is_file():
            build_fixtures()
        words = load_words_file(src)
        write_hex(words, args.out_dir)
        print(f"packed demo {args.demo} ({len(words)} words) -> {args.out_dir}")
        return 0

    values: list[int] = []
    if args.file:
        values = load_words_file(args.file)
    else:
        for w in args.words:
            values.append(int(w, 16))

    if not values:
        print("no words (use --build-fixtures, --demo, -f, or positional hex)", file=sys.stderr)
        return 1

    write_hex(values, args.out_dir)
    print(f"packed {len(values)} words -> {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
