"""ALU operation signatures and truth-table builder for decode search."""
from __future__ import annotations

from alu8_cases import CASES, LOGIC_C

PROFILE_LEGACY = "legacy"
PROFILE_Y_MUX = "y_mux"
PROFILE_MINIMAL = "minimal"
PROFILE_LGC_DIRECT = "lgc_direct"
PROFILES = (PROFILE_LEGACY, PROFILE_Y_MUX, PROFILE_MINIMAL, PROFILE_LGC_DIRECT)

OP_NAMES = [name for name, *_ in CASES]

LOGIC_OPS = ("AND", "OR", "XOR", "NOT", "PASS_A", "PASS_B")
ARITH_OPS = ("NOP", "ADD", "SUB", "CMP", "INC", "DEC")

# alu_op[0]->lgc3, alu_op[1]->lgc2, alu_op[2]->lgc1, alu_op[3]->lgc0 (breadboard direct wire)
def encode_lgc_direct(lgc: tuple[int, int, int, int]) -> int:
    l0, l1, l2, l3 = lgc
    return (l0 << 3) | (l1 << 2) | (l2 << 1) | l3


def lgc_from_opcode_direct(op: int) -> tuple[int, int, int, int]:
    return ((op >> 3) & 1, (op >> 2) & 1, (op >> 1) & 1, op & 1)


def lgc_direct_logic_assignment() -> dict[str, int]:
    """Fixed opcodes where alu_op bits wire straight to lgc (no lgc decode)."""
    out: dict[str, int] = {}
    for name in LOGIC_OPS:
        idx = OP_NAMES.index(name)
        lgc = LOGIC_C.get(idx, (0, 0, 0, 0))
        out[name] = encode_lgc_direct(lgc)
    return out


def logic_reserved_codes() -> set[int]:
    return set(lgc_direct_logic_assignment().values())


ARITH_GROUPS: dict[str, list[str]] = {
    "zero": ["NOP", "ADD"],
    "sub": ["SUB"],
    "cmp": ["CMP"],
    "inc": ["INC"],
    "dec": ["DEC"],
}

# Canonical control signature per operation (before opcode assignment).
# Tuple: (cin, b_sel, b_const_sel, lgc0, lgc1, lgc2, lgc3, y_mux)
_SIGNATURES: dict[str, tuple[int, ...]] = {
    "NOP": (0, 0, 0, 0, 0, 0, 0, 0),
    "ADD": (0, 0, 0, 0, 0, 0, 0, 0),
    "SUB": (1, 1, 0, 0, 0, 0, 0, 0),
    "AND": (0, 0, 0, 0, 0, 0, 1, 1),
    "OR": (0, 0, 0, 0, 1, 1, 1, 1),
    "XOR": (0, 0, 0, 0, 1, 1, 0, 1),
    "NOT": (0, 0, 0, 1, 0, 0, 0, 1),
    "PASS_A": (0, 0, 0, 0, 0, 0, 1, 1),
    "PASS_B": (0, 0, 0, 0, 0, 0, 1, 1),
    "INC": (0, 0, 1, 0, 0, 0, 0, 0),
    "DEC": (0, 1, 1, 0, 0, 0, 0, 0),
    "CMP": (1, 1, 0, 0, 0, 0, 0, 0),
}

def _legacy_s0_s1_from_op(name: str) -> tuple[int, int]:
    idx = OP_NAMES.index(name)
    _n, _a, _b, _y, c = CASES[idx]
    return int(c.get("net_153_s0", 0)), int(c.get("net_153_s1", 0))


def signature(name: str) -> tuple[int, ...]:
    if name not in _SIGNATURES:
        raise KeyError(name)
    return _SIGNATURES[name]


def signature_groups() -> dict[tuple[int, ...], list[str]]:
    groups: dict[tuple[int, ...], list[str]] = {}
    for name in OP_NAMES:
        sig = signature(name)
        groups.setdefault(sig, []).append(name)
    return groups


def current_assignment() -> dict[str, int]:
    return {name: idx for idx, name in enumerate(OP_NAMES)}


def build_assignment_from_codes(codes_by_sig: dict[tuple[int, ...], int]) -> dict[str, int]:
    """Map each operation to an alu_op code via its signature group."""
    out: dict[str, int] = {}
    for sig, names in signature_groups().items():
        code = codes_by_sig[sig]
        for name in names:
            out[name] = code
    return out


def _control_row(name: str, profile: str) -> dict[str, int]:
    cin, b_sel, b_cst, l0, l1, l2, l3, y_mux = signature(name)
    row: dict[str, int] = {
        "net_cin": cin,
        "net_b_sel": b_sel,
        "net_b_const_sel": b_cst,
        "net_lgc0": l0,
        "net_lgc1": l1,
        "net_lgc2": l2,
        "net_lgc3": l3,
    }
    if profile == PROFILE_LEGACY:
        s0, s1 = _legacy_s0_s1_from_op(name)
        row["net_153_s0"] = s0
        row["net_153_s1"] = s1
        row["b_const_hi"] = 1 if name == "DEC" else 0
    elif profile == PROFILE_Y_MUX:
        row["net_y_mux_sel"] = y_mux
        row["b_const_hi"] = 1 if name == "DEC" else 0
    elif profile == PROFILE_LGC_DIRECT:
        if name in LOGIC_OPS:
            code = encode_lgc_direct((l0, l1, l2, l3))
            row["net_lgc0"], row["net_lgc1"], row["net_lgc2"], row["net_lgc3"] = lgc_from_opcode_direct(
                code
            )
        # arithmetic: lgc not driven by decode (forced 0 in datapath); rows stay 0
    return row


def _validate_lgc_direct_assignment(assignment: dict[str, int]) -> None:
    fixed = lgc_direct_logic_assignment()
    for name, code in fixed.items():
        if assignment.get(name) != code:
            raise ValueError(
                f"lgc_direct: {name} must be opcode {code:#x}, got {assignment.get(name)}"
            )


def build_table(
    assignment: dict[str, int],
    profile: str = PROFILE_Y_MUX,
) -> tuple[list[dict], int | None]:
    """Build 16-row decode truth table. Returns (rows, cmp_op)."""
    if profile not in PROFILES:
        raise ValueError(profile)

    if profile == PROFILE_LGC_DIRECT:
        _validate_lgc_direct_assignment(assignment)

    code_to_ctrl: dict[int, dict[str, int]] = {}
    for name, code in assignment.items():
        row = _control_row(name, profile)
        if code in code_to_ctrl and code_to_ctrl[code] != row:
            raise ValueError(f"code {code}: conflicting controls for {name}")
        code_to_ctrl[code] = row

    cmp_op = assignment.get("CMP")
    sub_op = assignment.get("SUB")
    if cmp_op is not None and sub_op is not None and cmp_op == sub_op:
        raise ValueError("CMP and SUB must use distinct alu_op codes (cmp_n decode)")

    nop = _control_row("NOP", profile)
    rows: list[dict] = []
    for op in range(16):
        base = dict(code_to_ctrl.get(op, nop))
        base["op"] = op
        rows.append(base)
    return rows, cmp_op


def profile_outputs(profile: str) -> list[str]:
    arith = ["net_cin", "net_b_sel", "net_b_const_sel"]
    lgc = ["net_lgc0", "net_lgc1", "net_lgc2", "net_lgc3"]
    if profile == PROFILE_LEGACY:
        return ["net_cin", "net_153_s0", "net_153_s1", "net_b_sel", "net_b_const_sel", *lgc]
    if profile == PROFILE_Y_MUX:
        return [*arith, *lgc, "net_y_mux_sel"]
    if profile == PROFILE_LGC_DIRECT:
        return arith
    return [*arith, *lgc]


def profile_options(profile: str) -> dict:
    if profile == PROFILE_LEGACY:
        return {"include_b_const_hi": True, "include_cmp_n": True}
    if profile == PROFILE_Y_MUX:
        return {"include_b_const_hi": True, "include_cmp_n": True}
    return {"include_b_const_hi": False, "include_cmp_n": True}


def merge_lgc_direct(arith_codes: dict[str, int]) -> dict[str, int]:
    """Combine fixed logic opcodes with arithmetic group codes."""
    assign = dict(lgc_direct_logic_assignment())
    for group, code in arith_codes.items():
        for name in ARITH_GROUPS[group]:
            assign[name] = code
    return assign


def default_lgc_direct_arith() -> dict[str, int]:
    """Best exhaustive layout (37 decode gates); SUB/CMP at 0x0B/0x0F."""
    return {
        "zero": 0x00,
        "sub": 0x0B,
        "cmp": 0x0F,
        "inc": 0x0D,
        "dec": 0x0E,
    }


def breaking_changes(assignment: dict[str, int]) -> list[str]:
    cur = current_assignment()
    return [f"{name}: {cur[name]} -> {assignment[name]}" for name in OP_NAMES if assignment[name] != cur[name]]


def assignment_notes(assignment: dict[str, int]) -> list[str]:
    notes: list[str] = []
    inv: dict[int, list[str]] = {}
    for name, code in assignment.items():
        inv.setdefault(code, []).append(name)
    for code in sorted(inv):
        names = inv[code]
        if len(names) > 1:
            notes.append(f"code {code}: shared by {', '.join(names)}")
    return notes


def verify_signatures_match_cases() -> None:
    """Ensure canonical signatures agree with LOGIC_C / ctrl for each op index."""
    for idx, (name, _a, _b, _y, c) in enumerate(CASES):
        cin, b_sel, b_cst, l0, l1, l2, l3, y_mux = signature(name)
        assert int(c.get("net_cin", 0)) == cin
        assert int(c.get("net_b_sel", 0)) == b_sel
        assert int(c.get("net_b_const_sel", 0)) == b_cst
        lgc = LOGIC_C.get(idx, (0, 0, 0, 0))
        assert (l0, l1, l2, l3) == lgc
        if y_mux:
            assert int(c.get("net_153_s0", 0)) or int(c.get("net_153_s1", 0))
