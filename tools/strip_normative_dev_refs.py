#!/usr/bin/env python3
"""One-shot helper: strip common dev-tool blocks from docs/normative (plan execution)."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NORMATIVE = ROOT / "docs" / "normative"
GATES = "../../developer/verification-gates.md"

REPLACEMENTS = [
    (
        re.compile(
            r"\n## 검증 명령\n\n```bash\n.*?```\n",
            re.DOTALL,
        ),
        f"\n## 사전 검증 (개발자)\n\nBreadboard 전 시뮬·회귀 명령: [{GATES}]({GATES}).\n\n",
    ),
    (
        re.compile(r"\n### 5\. VM / bring-up\n\n.*?(?=\n---|\n## )", re.DOTALL),
        "\n### 5. Bring-up\n\nHardware gate: oscilloscope / LED observation per milestone checklist.\n\n",
    ),
    (
        re.compile(r"\n### Logic VM procedure\n\n.*?(?=\n### |\n## )", re.DOTALL),
        "",
    ),
    (
        re.compile(
            r"\n### Scenario sketch \(`hw/scenarios/vm/`\)\n\n```yaml\n.*?```\n",
            re.DOTALL,
        ),
        "",
    ),
]


def main() -> None:
    for path in sorted(NORMATIVE.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        orig = text
        for pattern, repl in REPLACEMENTS:
            text = pattern.sub(repl, text)
        if text != orig:
            path.write_text(text, encoding="utf-8", newline="\n")
            print("updated", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
