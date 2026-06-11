"""Two-pass assembler."""

from __future__ import annotations

from dataclasses import dataclass, field

from plover_asm.lexer import Token, tokenize
from plover_asm.opcodes import MNEMONICS, PSEUDO


def parse_num(s: str) -> int:
    s = s.strip()
    if s.startswith("$"):
        return int(s[1:], 16)
    if s.lower().startswith("0x"):
        return int(s, 16)
    return int(s, 0)


@dataclass
class AsmResult:
    bytes: list[int] = field(default_factory=list)
    symbols: dict[str, int] = field(default_factory=dict)
    listing: list[str] = field(default_factory=list)
    origin: int = 0


class Assembler:
    def __init__(self, text: str) -> None:
        self.text = text
        self.tokens = tokenize(text)
        self.pos = 0
        self.equates: dict[str, int] = {}
        self.symbols: dict[str, int] = {}
        self.origin = 0
        self.pc = 0
        self.out: list[int] = []
        self.listing: list[str] = []

    def _peek(self) -> Token | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _advance(self) -> Token:
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def _resolve(self, name: str) -> int:
        u = name.upper()
        if u in self.equates:
            return self.equates[u]
        if u in self.symbols:
            return self.symbols[u]
        raise KeyError(f"undefined symbol: {name}")

    def _emit(self, b: int) -> None:
        self.out.append(b & 0xFF)

    def _emit_word(self, w: int) -> None:
        self._emit(w & 0xFF)
        self._emit((w >> 8) & 0xFF)

    def _skip_operand_pass1(self) -> None:
        t = self._peek()
        if t is None:
            return
        if t.kind == "NUM":
            self._advance()
        elif t.kind in ("IDENT", "LABEL_REF"):
            self._advance()

    def _operand(self) -> int:
        t = self._peek()
        if t is None:
            return 0
        if t.kind == "NUM":
            self._advance()
            return parse_num(t.value) & 0xFFFF
        if t.kind in ("IDENT", "LABEL_REF"):
            self._advance()
            return self._resolve(t.value) & 0xFFFF
        return 0

    def _line_pass1(self) -> None:
        while self.pos < len(self.tokens):
            t = self._peek()
            if t is None:
                break
            if t.kind == "LABEL_DEF":
                self._advance()
                self.symbols[t.value] = self.pc
                continue
            if t.kind == "PSEUDO":
                pseudo = self._advance().value
                if pseudo == "ORG":
                    self.origin = self.pc = parse_num(self._advance().value)
                elif pseudo == "EQU":
                    name = self._advance().value
                    t = self._peek()
                    if t and t.kind == "NUM":
                        self.equates[name.upper()] = parse_num(self._advance().value)
                    else:
                        self._skip_operand_pass1()
                elif pseudo == "DB":
                    while True:
                        tok = self._peek()
                        if tok is None or tok.kind in ("LABEL_DEF", "MNEM", "PSEUDO"):
                            break
                        if tok.kind == "STRING":
                            self._advance()
                            for _ch in tok.value:
                                self.pc += 1
                        else:
                            self.pc += 1
                            self._skip_operand_pass1()
                        if self._peek() and self._peek().kind == "COMMA":
                            self._advance()
                elif pseudo == "DW":
                    self.pc += 2
                    self._skip_operand_pass1()
                continue
            if t.kind == "MNEM":
                mnem = self._advance().value
                op = MNEMONICS[mnem]
                if mnem in ("RET", "HALT", "ADD_RR"):
                    self.pc += 1
                elif mnem in ("JMP", "BEQ", "CALL", "STA16"):
                    self.pc += 3
                else:
                    self.pc += 2
                if mnem not in ("RET", "HALT"):
                    self._skip_operand_pass1()
                continue
            self._advance()

    def _line_pass2(self) -> None:
        self.pos = 0
        self.pc = self.origin
        while self.pos < len(self.tokens):
            t = self._peek()
            if t is None:
                break
            start_pc = self.pc
            line_bytes: list[int] = []
            if t.kind == "LABEL_DEF":
                self._advance()
                continue
            if t.kind == "PSEUDO":
                pseudo = self._advance().value
                if pseudo == "ORG":
                    val = parse_num(self._advance().value)
                    while self.pc < val:
                        self._emit(0)
                        self.pc += 1
                    self.pc = val
                    self.origin = val
                elif pseudo == "EQU":
                    self._advance()
                    self._operand()
                elif pseudo == "DB":
                    while True:
                        tok = self._peek()
                        if tok is None or tok.kind in ("LABEL_DEF", "MNEM", "PSEUDO"):
                            break
                        if tok.kind == "STRING":
                            self._advance()
                            for ch in tok.value:
                                self._emit(ord(ch))
                                line_bytes.append(ord(ch))
                        else:
                            v = self._operand() & 0xFF
                            self._emit(v)
                            line_bytes.append(v)
                    self.pc = start_pc + len(line_bytes)
                elif pseudo == "DW":
                    w = self._operand()
                    self._emit_word(w)
                    line_bytes.extend([w & 0xFF, (w >> 8) & 0xFF])
                    self.pc = start_pc + 2
                if line_bytes or pseudo == "ORG":
                    hexpart = " ".join(f"{b:02X}" for b in line_bytes)
                    self.listing.append(f"{start_pc:04X}  {hexpart}")
                continue
            if t.kind == "MNEM":
                mnem = self._advance().value
                op = MNEMONICS[mnem]
                if mnem in ("RET", "HALT", "ADD_RR"):
                    self._emit(op)
                    line_bytes.append(op)
                    self.pc = start_pc + 1
                elif mnem in ("JMP", "BEQ", "CALL", "STA16"):
                    self._emit(op)
                    imm = self._operand() & 0xFFFF
                    self._emit(imm & 0xFF)
                    self._emit((imm >> 8) & 0xFF)
                    line_bytes.extend([op, imm & 0xFF, (imm >> 8) & 0xFF])
                    self.pc = start_pc + 3
                else:
                    self._emit(op)
                    imm = self._operand() & 0xFF
                    self._emit(imm)
                    line_bytes.extend([op, imm])
                    self.pc = start_pc + 2
                hexpart = " ".join(f"{b:02X}" for b in line_bytes)
                self.listing.append(f"{start_pc:04X}  {hexpart}  {mnem}")
                continue
            self._advance()

    def run(self) -> AsmResult:
        self._line_pass1()
        self.pos = 0
        self.pc = self.origin
        self.out = []
        self._line_pass2()
        return AsmResult(
            bytes=self.out,
            symbols=dict(self.symbols),
            listing=self.listing,
            origin=self.origin,
        )


def assemble(text: str, origin: int = 0) -> AsmResult:
    a = Assembler(text)
    a.origin = a.pc = origin
    return a.run()


def assemble_file(path: str, origin: int = 0) -> AsmResult:
    from pathlib import Path

    text = Path(path).read_text(encoding="utf-8")
    return assemble(text, origin=origin)
