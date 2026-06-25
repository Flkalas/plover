#!/usr/bin/env python3
"""Second-pass cleanup for normative docs during governance migration."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NORMATIVE = ROOT / "docs" / "normative"
GATES = "../../developer/verification-gates.md"

# Remove fenced bash blocks that mention hwsim/pytest/plover_vm/cargo
DEV_BLOCK = re.compile(
    r"```(?:bash|sh)?\n(?:.*(?:hwsim|pytest|plover_vm|cargo run).*\n)+```\n?",
    re.MULTILINE | re.IGNORECASE,
)

SUBS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"`python -m hwsim[^`\n]*`"), "developer verification gate"),
    (re.compile(r"python -m hwsim[^\n]*\n?", re.I), ""),
    (re.compile(r"python -m pytest[^\n]*\n?", re.I), ""),
    (re.compile(r"python -m plover_vm[^\n]*\n?", re.I), ""),
    (re.compile(r"cargo run -p plover_vm[^\n]*\n?", re.I), ""),
    (re.compile(r"python -m cyclesim[^\n]*\n?", re.I), ""),
    (re.compile(r"\bhwsim\b", re.I), "pre-flight sim"),
    (re.compile(r"\bpytest\b", re.I), "regression"),
    (re.compile(r"`plover_vm[^`]*`", re.I), "logic VM (developer)"),
    (re.compile(r"\bplover_vm\b", re.I), "logic VM"),
    (re.compile(r"\bcyclesim\b", re.I), "cycle sim"),
    (re.compile(r"\*\*VM만:\*\*[^|]*"), "**비실기:** reserved opcode namespace only"),
    (re.compile(r"VM fast path[^.]*\."), "미패킹 상태."),
    (re.compile(r"또는 \*\*VM만\*\*[^.]*\."), "소프트웨어 다중 스텝으로 처리."),
    (re.compile(r"\[hardware-architecture-synthesis\.md\]\([^)]*research[^)]*\)"), "[microcode-spec.md](../hardware/microcode-spec.md)"),
    (re.compile(r"\[isa\.py\]\([^)]*plover_vm[^)]*\)"), "[microcode-spec.md](../hardware/microcode-spec.md)"),
    (re.compile(r"`test_call_ret\.py`"), "S2 bring-up checklist"),
    (re.compile(r"`test_[^`]+`"), "milestone checklist"),
    (re.compile(r"--engine micro", re.I), "breadboard ISA"),
    (re.compile(r"\[hw-sim\.md\]\([^)]*\)"), f"[verification-gates.md]({GATES})"),
    (re.compile(r"\[implementation-plan-v1\.0\.md\]\(\.\./project/"), "[implementation-plan-v1.0.md](../../developer/project/"),
    (re.compile(r"\(research/[^)]+\)"), "(see developer docs)"),
    (re.compile(r"\.\./hardware/research/[^\s\])]+"), "developer research index"),
    (re.compile(r"hardware/research/[^\s\])]+"), "developer research index"),
    (re.compile(r"\| Research \| \[.*hardware/research.*\|"), "| Research | docs/hardware/research/ (not normative) |"),
]


def main() -> None:
    for path in sorted(NORMATIVE.rglob("*.md")):
        if path.name == "fpga-target-guide.md":
            continue  # manual
        text = path.read_text(encoding="utf-8")
        orig = text
        text = DEV_BLOCK.sub("", text)
        for pattern, repl in SUBS:
            text = pattern.sub(repl, text)
        # collapse excessive blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        if text != orig:
            path.write_text(text, encoding="utf-8", newline="\n")
            print("updated", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
