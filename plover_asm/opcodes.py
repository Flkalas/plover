"""Normative macro opcodes — single source with plover_vm.macro.isa."""

from plover_vm.macro.isa import (
    OP_ADD,
    OP_ADD_RR,
    OP_BCS,
    OP_BEQ,
    OP_CALL,
    OP_CMP,
    OP_HALT,
    OP_JMP,
    OP_LDA,
    OP_LDIO,
    OP_MOV,
    OP_RET,
    OP_STA,
    OP_STA16,
    OP_STIO,
)

MNEMONICS: dict[str, int] = {
    "ADD": OP_ADD,
    "LDA": OP_LDA,
    "STA": OP_STA,
    "BEQ": OP_BEQ,
    "JMP": OP_JMP,
    "CALL": OP_CALL,
    "RET": OP_RET,
    "LDIO": OP_LDIO,
    "STIO": OP_STIO,
    "HALT": OP_HALT,
    "ADD_RR": OP_ADD_RR,
    "MOV": OP_MOV,
    "CMP": OP_CMP,
    "BCS": OP_BCS,
    "STA16": OP_STA16,
}

PSEUDO = frozenset({"ORG", "EQU", "DB", "DW"})

TWO_BYTE_OPS = frozenset(MNEMONICS.keys()) - {"RET", "HALT", "ADD_RR"}
