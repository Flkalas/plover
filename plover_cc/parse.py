"""Extremely small Subset-C parser for v0.1 bring-up (S5).

This is intentionally minimal: it supports a tiny 'smoke' subset and produces a
simple IR used by codegen.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Program:
    return_value: int


def parse(text: str) -> Program:
    # Accept patterns like:
    #   int main(void) { return add(2, 3); }
    # or:
    #   int main(void) { return 5; }
    m = re.search(r"return\s+([0-9]+)\s*;", text)
    if m:
        return Program(return_value=int(m.group(1), 10))

    m = re.search(r"return\s+add\s*\(\s*([0-9]+)\s*,\s*([0-9]+)\s*\)\s*;", text)
    if m:
        a = int(m.group(1), 10)
        b = int(m.group(2), 10)
        return Program(return_value=a + b)

    raise ValueError("unsupported subset-c program (expected return <int> or return add(<int>,<int>))")

