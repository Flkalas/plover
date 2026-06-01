#!/usr/bin/env python3
"""Tiny demo runner for the S3 Forth core."""

from __future__ import annotations

import argparse

from forth.interpreter import Forth


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval", action="append", default=[], help="Line to evaluate (repeatable)")
    args = ap.parse_args()

    f = Forth()
    for line in args.eval or [": SQUARE DUP * ;", "5 SQUARE ."]:
        f.eval_line(line)
    for s in f.output:
        print(s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

