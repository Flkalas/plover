"""Normative microcode-spec.md vs pack_control_store.py alignment."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_verify_control_store_script() -> None:
    r = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "verify_control_store.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stdout + r.stderr


def test_cw_hex_matches_packer() -> None:
    from tools.pack_control_store import build_all

    hex_path = ROOT / "hw" / "fixtures" / "control" / "cw.hex"
    assert hex_path.is_file()
    words = [int(line.strip(), 16) for line in hex_path.read_text().splitlines() if line.strip()]
    assert words == build_all()
