#!/usr/bin/env python3
"""Generate CPLD control research netlists and static unit viewers."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ARCHES = (
    ("counter_template", "cpld_ctrl_counter", "CPLD control - counter + template decode"),
    ("flash_cw16_direct", "cpld_ctrl_cw16", "CPLD control - Flash CW16 direct"),
)

BUILD_ROOT = ROOT / "build" / "research" / "cpld-ctrl-extract"
DOCS_ROOT = ROOT / "docs" / "hardware" / "research" / "cpld-ctrl-extract" / "viewers"


def _run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


def build(arch: str | None = None) -> None:
    gen = [sys.executable, "tools/gen_cpld_ctrl_netlist.py"]
    if arch:
        gen.extend(["--arch", arch])
    _run(gen)

    for arch_id, stem, title in ARCHES:
        if arch and arch != arch_id:
            continue
        nl = ROOT / "hw" / "netlist" / "research" / f"{stem}.yaml"
        cat = ROOT / "hw" / "units" / "research" / f"{stem}.yaml"
        out = BUILD_ROOT / arch_id
        _run(
            [
                sys.executable,
                "-m",
                "hwsim",
                "export-units",
                str(nl.relative_to(ROOT)),
                "--catalog",
                str(cat.relative_to(ROOT)),
                "-o",
                str(out.relative_to(ROOT)),
                "--html",
                "--embed-manifest",
                "--title",
                title,
            ]
        )
        docs_out = DOCS_ROOT / arch_id
        if docs_out.exists():
            shutil.rmtree(docs_out)
        shutil.copytree(out, docs_out)
        print(f"Copied viewer to {docs_out}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--arch",
        choices=[a[0] for a in ARCHES],
        help="Build one architecture only",
    )
    args = p.parse_args()
    build(args.arch)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
