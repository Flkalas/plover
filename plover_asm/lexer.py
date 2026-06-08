"""Tokenize assembler source."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Token:
    kind: str  # MNEM, NUM, LABEL_DEF, LABEL_REF, COMMA, STRING
    value: str
    line: int


def tokenize(text: str) -> list[Token]:
    tokens: list[Token] = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        pos = 0
        while pos < len(line):
            m = re.match(r"\s+", line[pos:])
            if m:
                pos += m.end()
                continue
            m = re.match(r"([A-Za-z_][A-Za-z0-9_]*):", line[pos:])
            if m:
                tokens.append(Token("LABEL_DEF", m.group(1).upper(), lineno))
                pos += m.end()
                continue
            m = re.match(r"\.(ORG|EQU|DB|DW)\b", line[pos:], re.I)
            if m:
                tokens.append(Token("PSEUDO", m.group(1).upper(), lineno))
                pos += m.end()
                continue
            m = re.match(r"0[xX][0-9A-Fa-f]+|\$[0-9A-Fa-f]+|\d+", line[pos:])
            if m:
                tokens.append(Token("NUM", m.group(0), lineno))
                pos += m.end()
                continue
            m = re.match(r'"([^"]*)"', line[pos:])
            if m:
                tokens.append(Token("STRING", m.group(1), lineno))
                pos += m.end()
                continue
            m = re.match(r"[A-Za-z_][A-Za-z0-9_]*", line[pos:])
            if m:
                word = m.group(0).upper()
                kind = "MNEM" if word in {
                    "ADD", "LDA", "STA", "BEQ", "JMP", "CALL", "RET",
                    "LDIO", "STIO", "STA16", "HALT", "ADD_RR", "MOV", "CMP", "BCS",
                } or word in {"ORG", "EQU", "DB", "DW"} else "IDENT"
                tokens.append(Token(kind, word, lineno))
                pos += m.end()
                continue
            raise SyntaxError(f"line {lineno}: bad token at {line[pos:]!r}")
    return tokens
