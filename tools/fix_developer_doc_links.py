#!/usr/bin/env python3
"""Fix relative links in docs/developer after normative split."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEV = ROOT / "docs" / "developer"

REPLS = [
    (re.compile(r"\]\(\.\./hardware/"), "](../../normative/hardware/"),
    (re.compile(r"\]\(\.\./hw-bringup/"), "](../../normative/hw-bringup/"),
    (re.compile(r"\]\(\.\./boot/"), "](../../normative/boot/"),
    (re.compile(r"\]\(\.\./copro/"), "](../../normative/copro/"),
    (re.compile(r"\]\(\.\./software/"), "](../../normative/software/"),
    (re.compile(r"\]\(\.\./project/parts-on-hand"), "](../../normative/project/parts-on-hand"),
    (re.compile(r"\]\(parts-on-hand\.md\)"), "](../../normative/project/parts-on-hand.md)"),
    (re.compile(r"\]\(\.\./archive/"), "](../../archive/"),
    (re.compile(r"\]\(\.\./BOM\.md\)"), "](../../../BOM.md)"),
]


def main() -> None:
    for path in sorted(DEV.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        orig = text
        for pattern, repl in REPLS:
            text = pattern.sub(repl, text)
        if text != orig:
            path.write_text(text, encoding="utf-8", newline="\n")
            print("fixed", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
