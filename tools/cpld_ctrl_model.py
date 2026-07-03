"""v1.0 CPLD FSM → (opcode, phase) control truth table for external-74HC search."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from alu_decode_model import OP_NAMES, signature

from pack_control_store import (  # noqa: E402 — tools/ on path
    ALU_ADD,
    ALU_CMP,
    ALU_NOP,
    ALU_SUB,
    FSM_OPCODE_TABLE,
    OP_ADD,
    OP_BEQ,
    OP_CMP,
    OP_HALT,
    OP_JMP,
    OP_LDA,
    OP_LDIO,
    OP_STA,
    OP_STA16,
    OP_STIO,
    cs_index,
    cs_index5,
)

IDX5_SLOTS = 128

# ALU_OP field in archived 10b CW maps to CASES index.
_ALU_OP_TO_NAME: dict[int, str] = {i: OP_NAMES[i] for i in range(len(OP_NAMES))}

OUTPUT_FIELDS = (
    "reg_we",
    "mem_rd",
    "mem_wr",
    "y_oe",
    "cin",
    "bctrl0",
    "bctrl1",
    "bctrl2",
    "bctrl3",
    "lgc0",
    "lgc1",
    "lgc2",
    "lgc3",
    "y_mux_sel",
    "w_sel0",
    "w_sel1",
    "xfer_src0",
    "xfer_src1",
    "pc_load_en",
)


@dataclass(frozen=True)
class CtrlRow:
    opcode: int
    phase: int
    template: str
    reg_we: int = 0
    mem_rd: int = 0
    mem_wr: int = 0
    y_oe: int = 0
    cin: int = 0
    bctrl0: int = 0
    bctrl1: int = 0
    bctrl2: int = 0
    bctrl3: int = 0
    lgc0: int = 0
    lgc1: int = 0
    lgc2: int = 0
    lgc3: int = 0
    y_mux_sel: int = 0
    w_sel: int = 0
    xfer_src: int = 0
    pc_load_en: int = 0
    pc_load_flg_z: bool = False
    alu_op: int = ALU_NOP

    @property
    def idx5(self) -> int:
        return cs_index5(self.opcode, self.phase)

    @property
    def idx4(self) -> int:
        return cs_index(self.opcode, self.phase)

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["idx5"] = self.idx5
        d["idx4"] = self.idx4
        return d

    def strobe_row(self, *, idx_key: str = "idx5") -> dict[str, int]:
        idx = self.idx5 if idx_key == "idx5" else self.idx4
        return {
            "idx": idx,
            "reg_we": self.reg_we,
            "mem_rd": self.mem_rd,
            "mem_wr": self.mem_wr,
            "y_oe": self.y_oe,
            "w_sel0": self.w_sel & 1,
            "w_sel1": (self.w_sel >> 1) & 1,
            "xfer_src0": self.xfer_src & 1,
            "xfer_src1": (self.xfer_src >> 1) & 1,
            "pc_load_en": self.pc_load_en,
        }


def _alu_from_op(alu_op: int) -> dict[str, int]:
    name = _ALU_OP_TO_NAME.get(alu_op, "NOP")
    cin, b0, b1, b2, b3, l0, l1, l2, l3, y_mux = signature(name)
    return {
        "cin": cin,
        "bctrl0": b0,
        "bctrl1": b1,
        "bctrl2": b2,
        "bctrl3": b3,
        "lgc0": l0,
        "lgc1": l1,
        "lgc2": l2,
        "lgc3": l3,
        "y_mux_sel": y_mux,
    }


def _legacy_cw16_b_fields(row: CtrlRow) -> tuple[int, int]:
    """Map 4-bit B_CTRL to archived Flash CW16 2-bit B mux select."""
    from alu8_cases import BCTRL_ADD, BCTRL_DEC

    bpat = (row.bctrl0, row.bctrl1, row.bctrl2, row.bctrl3)
    return (
        1 if bpat == BCTRL_ADD else 0,
        1 if bpat == BCTRL_DEC else 0,
    )



def _alu_reg_rows(op: int, alu_op: int, *, final_w_sel: int) -> list[CtrlRow]:
    y_on = 1 if alu_op != ALU_CMP else 0
    rows: list[CtrlRow] = []
    for ph in range(3):
        if alu_op == ALU_CMP and ph == 2:
            row = CtrlRow(
                opcode=op,
                phase=ph,
                template="ALU_REG",
                alu_op=ALU_NOP,
                **_alu_from_op(ALU_NOP),
            )
        else:
            reg_we = 1 if ph == 2 else 0
            w_sel = final_w_sel if ph == 2 else (1 if op == OP_ADD and ph == 1 else 0)
            row = CtrlRow(
                opcode=op,
                phase=ph,
                template="ALU_REG",
                y_oe=y_on,
                reg_we=reg_we,
                w_sel=w_sel,
                alu_op=alu_op,
                **_alu_from_op(alu_op),
            )
        rows.append(row)
    return rows


def _mem_ld_rows(op: int) -> list[CtrlRow]:
    nop = _alu_from_op(ALU_NOP)
    return [
        CtrlRow(opcode=op, phase=0, template="MEM_LD", mem_rd=1, alu_op=ALU_NOP, **nop),
        CtrlRow(
            opcode=op,
            phase=1,
            template="MEM_LD",
            reg_we=1,
            w_sel=0,
            alu_op=ALU_NOP,
            **nop,
        ),
    ]


def _mem_st_rows(op: int) -> list[CtrlRow]:
    nop = _alu_from_op(ALU_NOP)
    return [
        CtrlRow(opcode=op, phase=0, template="MEM_ST", y_oe=1, alu_op=ALU_NOP, **nop),
        CtrlRow(opcode=op, phase=1, template="MEM_ST", mem_wr=1, alu_op=ALU_NOP, **nop),
    ]


def _xfer_row(op: int, src: int, dst: int) -> list[CtrlRow]:
    nop = _alu_from_op(ALU_NOP)
    return [
        CtrlRow(
            opcode=op,
            phase=0,
            template="XFER",
            reg_we=1,
            w_sel=dst,
            xfer_src=src,
            alu_op=ALU_NOP,
            **nop,
        ),
    ]


def _beq_rows(op: int) -> list[CtrlRow]:
    sub = _alu_from_op(ALU_SUB)
    nop = _alu_from_op(ALU_NOP)
    return [
        CtrlRow(opcode=op, phase=0, template="BEQ", alu_op=ALU_SUB, **sub),
        CtrlRow(
            opcode=op,
            phase=1,
            template="BEQ",
            pc_load_en=1,
            pc_load_flg_z=True,
            alu_op=ALU_NOP,
            **nop,
        ),
    ]


def _jmp_row(op: int) -> list[CtrlRow]:
    nop = _alu_from_op(ALU_NOP)
    return [
        CtrlRow(
            opcode=op,
            phase=0,
            template="JMP",
            pc_load_en=1,
            alu_op=ALU_NOP,
            **nop,
        ),
    ]


def _halt_row(op: int) -> list[CtrlRow]:
    nop = _alu_from_op(ALU_NOP)
    return [CtrlRow(opcode=op, phase=0, template="HALT", alu_op=ALU_NOP, **nop)]


def _rows_for_opcode(op: int, meta: dict) -> list[CtrlRow]:
    tmpl = meta["template"]
    if tmpl == "ALU_REG":
        alu_op = ALU_ADD if op == OP_ADD else ALU_CMP
        return _alu_reg_rows(op, alu_op, final_w_sel=int(meta.get("w_sel", 2)))
    if tmpl == "MEM_LD":
        return _mem_ld_rows(op)
    if tmpl == "MEM_ST":
        return _mem_st_rows(op)
    if tmpl == "XFER":
        return _xfer_row(op, int(meta["src"]), int(meta["dst"]))
    if tmpl == "BEQ":
        return _beq_rows(op)
    if tmpl == "JMP":
        return _jmp_row(op)
    if tmpl == "HALT":
        return _halt_row(op)
    raise ValueError(f"unknown template {tmpl!r} for opcode 0x{op:02X}")


def build_v10_ctrl_table() -> list[CtrlRow]:
    rows: list[CtrlRow] = []
    for op in sorted(FSM_OPCODE_TABLE):
        rows.extend(_rows_for_opcode(op, FSM_OPCODE_TABLE[op]))
    return rows


def active_idx5_slots(rows: list[CtrlRow] | None = None) -> list[int]:
    rows = rows or build_v10_ctrl_table()
    return sorted({r.idx5 for r in rows})


def active_idx4_slots(rows: list[CtrlRow] | None = None) -> list[int]:
    rows = rows or build_v10_ctrl_table()
    return sorted({r.idx4 for r in rows})


def idx_truth_table(
    rows: list[CtrlRow],
    outputs: list[str],
    *,
    idx_key: str = "idx5",
    slot_count: int = IDX5_SLOTS,
) -> list[dict[str, int]]:
    """Sparse table expanded to fixed slot count for SOP scoring."""
    by_idx: dict[int, dict[str, int]] = {}
    for row in rows:
        st = row.strobe_row(idx_key=idx_key)
        idx = st["idx"]
        by_idx[idx] = st
    out: list[dict[str, int]] = []
    for idx in range(slot_count):
        base = dict(by_idx.get(idx, {"idx": idx}))
        base["idx"] = idx
        for sig in outputs:
            base.setdefault(sig, 0)
        out.append(base)
    return out


def strobe_truth_table(
    outputs: list[str] | None = None,
    *,
    idx_key: str = "idx5",
) -> list[dict[str, int]]:
    outputs = outputs or [
        "reg_we",
        "mem_rd",
        "mem_wr",
        "y_oe",
        "w_sel0",
        "w_sel1",
        "xfer_src0",
        "xfer_src1",
        "pc_load_en",
    ]
    rows = build_v10_ctrl_table()
    slot_count = 128 if idx_key == "idx5" else 64
    return idx_truth_table(rows, outputs, idx_key=idx_key, slot_count=slot_count)


def alu_truth_table(
    rows: list[CtrlRow] | None = None,
    *,
    idx_key: str = "idx5",
) -> list[dict[str, int]]:
    """Per-slot ALU direct controls (CPLD FSM output style)."""
    rows = rows or build_v10_ctrl_table()
    outputs = [
        "cin",
        "bctrl0",
        "bctrl1",
        "bctrl2",
        "bctrl3",
        "lgc0",
        "lgc1",
        "lgc2",
        "lgc3",
        "y_mux_sel",
    ]
    slot_count = 128 if idx_key == "idx5" else 64
    by_idx: dict[int, dict[str, int]] = {}
    for row in rows:
        idx = row.idx5 if idx_key == "idx5" else row.idx4
        by_idx[idx] = {"idx": idx, **{sig: getattr(row, sig) for sig in outputs}}
    out: list[dict[str, int]] = []
    for idx in range(slot_count):
        base = dict(by_idx.get(idx, {"idx": idx}))
        base["idx"] = idx
        for sig in outputs:
            base.setdefault(sig, 0)
        out.append(base)
    return out


def flash_cw10_rows(rows: list[CtrlRow] | None = None) -> list[dict[str, int]]:
    """Archived 10b CW: alu_op + strobes per idx4 slot."""
    rows = rows or build_v10_ctrl_table()
    out: list[dict[str, int]] = []
    for row in rows:
        out.append(
            {
                "idx": row.idx4,
                "alu_op": row.alu_op,
                "reg_we": row.reg_we,
                "y_oe": row.y_oe,
                "mem_rd": row.mem_rd,
                "mem_wr": row.mem_wr,
            }
        )
    return idx_truth_table(
        rows,
        ["alu_op", "reg_we", "y_oe", "mem_rd", "mem_wr"],
        idx_key="idx4",
        slot_count=64,
    )
