"""Golden FSM control strobes from simulators/cyclesim.data.fsm_table."""

from __future__ import annotations

from simulators.cyclesim.data.isa import decode_tfr, is_tfr_valid

# ctrl_lut.inc LUT outputs (merged reg_we / w_sel / bctrl fanout are in system_ctrl.pld)
FSM_OUTPUT_SIGNALS = (
    "reg_we_lut",
    "mem_rd",
    "mem_wr",
    "y_oe",
    "w_sel0_lut",
    "w_sel1_lut",
    "cin",
    "bctrl0",
    "bctrl2",
    "lgc0",
    "lgc1",
    "lgc2",
    "lgc3",
    "s0",
    "s1",
    "lut_pc_load",
    "lut_pc_flg_z",
    "flg_we",
)

# cyclesim CtrlLookup merged outputs (TFR comb overlay when no table row)
CYCLESIM_NET_MAP: dict[str, str] = {
    "reg_we": "net_reg_we",
    "mem_rd": "net_mem_rd",
    "mem_wr": "net_mem_wr",
    "y_oe": "net_y_oe",
    "w_sel0": "net_w_sel0",
    "w_sel1": "net_w_sel1",
    "cin": "net_cin",
    "bctrl0": "net_bctrl0",
    "bctrl1": "net_bctrl1",
    "bctrl2": "net_bctrl2",
    "bctrl3": "net_bctrl3",
    "lgc0": "net_lgc0",
    "lgc1": "net_lgc1",
    "lgc2": "net_lgc2",
    "lgc3": "net_lgc3",
    "s0": "net_153_s0",
    "s1": "net_153_s1",
    "lut_pc_load": "net_pc_load_en",
    "lut_pc_flg_z": "net_pc_load_flg_z",
    "flg_we": "net_flg_we",
}

# Tier C external 574 CW latch (control-word-latch.md sec 4)
CW_LO_BITS: tuple[str, ...] = (
    "mem_rd",
    "mem_wr",
    "y_oe",
    "flg_we",
    "pc_load_en",
    "cin",
    "bctrl0",
    "bctrl2",
)
CW_HI_BITS: tuple[str, ...] = (
    "lgc0",
    "lgc1",
    "lgc2",
    "lgc3",
    "s0",
    "s1",
)

CSIM_INPUT_ORDER = (
    "clk",
    "opc0",
    "opc1",
    "opc2",
    "opc3",
    "opc4",
    "ph0",
    "ph1",
    "flg_z",
    "flg_c",
    "d_in0",
    "d_in1",
    "d_in2",
    "d_in3",
    "d_in4",
    "d_in5",
    "d_in6",
    "d_in7",
)


def row_bools(row) -> dict[str, bool]:
    return {
        "reg_we_lut": row.reg_we,
        "mem_rd": row.mem_rd,
        "mem_wr": row.mem_wr,
        "y_oe": row.y_oe,
        "w_sel0_lut": bool(row.w_sel & 1),
        "w_sel1_lut": bool((row.w_sel >> 1) & 1),
        "cin": bool(row.alu.cin),
        "bctrl0": bool((row.alu.bctrl >> 0) & 1),
        "bctrl2": bool((row.alu.bctrl >> 2) & 1),
        "lgc0": bool((row.alu.lgc >> 0) & 1),
        "lgc1": bool((row.alu.lgc >> 1) & 1),
        "lgc2": bool((row.alu.lgc >> 2) & 1),
        "lgc3": bool((row.alu.lgc >> 3) & 1),
        "s0": bool(row.alu.s0),
        "s1": bool(row.alu.s1),
        "lut_pc_load": row.pc_load_en,
        "lut_pc_flg_z": row.pc_load_flg_z,
        "flg_we": row.flg_we,
    }


def tfr_valid(opcode: int) -> bool:
    return is_tfr_valid(opcode)


def merge_lut_strobes(lut: dict[str, bool], opcode: int) -> dict[str, bool]:
    """Apply system_ctrl.pld merge: reg_we_lut|TFR, w_sel mux, bctrl fanout."""
    op = opcode & 0x1F
    tfr = is_tfr_valid(opcode)
    b0 = lut["bctrl0"]
    b2 = lut["bctrl2"]
    merged = {
        "reg_we": lut["reg_we_lut"] or tfr,
        "mem_rd": lut["mem_rd"],
        "mem_wr": lut["mem_wr"],
        "y_oe": lut["y_oe"],
        "w_sel0": bool(tfr and ((op >> 2) & 1)) or (not tfr and lut["w_sel0_lut"]),
        "w_sel1": bool(tfr and ((op >> 3) & 1)) or (not tfr and lut["w_sel1_lut"]),
        "cin": lut["cin"],
        "bctrl0": b0,
        "bctrl1": b0,
        "bctrl2": b2,
        "bctrl3": b2,
        "lgc0": lut["lgc0"],
        "lgc1": lut["lgc1"],
        "lgc2": lut["lgc2"],
        "lgc3": lut["lgc3"],
        "s0": lut["s0"],
        "s1": lut["s1"],
        "lut_pc_load": lut["lut_pc_load"],
        "lut_pc_flg_z": lut["lut_pc_flg_z"],
        "flg_we": lut["flg_we"],
    }
    return merged


def pack_cw_byte(merged: dict[str, bool], bit_names: tuple[str, ...]) -> int:
    value = 0
    for i, name in enumerate(bit_names):
        if merged.get(name, False):
            value |= 1 << i
    return value


def pack_cw_lo(merged: dict[str, bool]) -> int:
    return pack_cw_byte(merged, CW_LO_BITS)


def pack_cw_hi(merged: dict[str, bool]) -> int:
    return pack_cw_byte(merged, CW_HI_BITS)


def merged_for_cw_pack(
    opcode: int,
    phase: int,
    *,
    macro_end: bool = False,
    flg_z: bool = False,
) -> dict[str, bool]:
    """Merged strobes including pc_load_en for CW_LO serialization."""
    lut = golden_for_opcode_phase(opcode, phase)
    merged = merge_lut_strobes(lut, opcode)
    merged["pc_load_en"] = pc_load_at_macro_end(lut, flg_z, macro_end=macro_end)
    return merged


def merged_bools(opcode: int, phase: int) -> dict[str, bool]:
    """LUT golden → PLD merge → merged pin strobes."""
    return merge_lut_strobes(golden_for_opcode_phase(opcode, phase), opcode)


def pc_load_at_macro_end(lut: dict[str, bool], flg_z: bool, macro_end: bool = True) -> bool:
    """system_ctrl.pld: pc_load_en = macro_end & lut_pc_load & (!lut_pc_flg_z | flg_z)."""
    if not macro_end or not lut["lut_pc_load"]:
        return False
    if lut["lut_pc_flg_z"]:
        return flg_z
    return True


def cyclesim_bools(opcode: int, phase: int) -> dict[str, bool]:
    """Merged strobes as cyclesim CtrlLookup drives them."""
    from simulators.cyclesim.data.fsm_table import lookup_row

    base = {sig: False for sig in CYCLESIM_NET_MAP}
    row = lookup_row(opcode, phase)
    if row is not None:
        base["reg_we"] = row.reg_we
        base["mem_rd"] = row.mem_rd
        base["mem_wr"] = row.mem_wr
        base["y_oe"] = row.y_oe
        base["w_sel0"] = bool(row.w_sel & 1)
        base["w_sel1"] = bool((row.w_sel >> 1) & 1)
        base["cin"] = bool(row.alu.cin)
        for i in range(4):
            base[f"bctrl{i}"] = bool((row.alu.bctrl >> i) & 1)
            base[f"lgc{i}"] = bool((row.alu.lgc >> i) & 1)
        base["s0"] = bool(row.alu.s0)
        base["s1"] = bool(row.alu.s1)
        base["lut_pc_load"] = row.pc_load_en
        base["lut_pc_flg_z"] = row.pc_load_flg_z
        base["flg_we"] = row.flg_we
    elif is_tfr_valid(opcode) and phase == 0:
        _src, dst = decode_tfr(opcode)
        base["reg_we"] = True
        base["w_sel0"] = bool(dst & 1)
        base["w_sel1"] = bool((dst >> 1) & 1)
    return base


def sim_env(opcode: int, phase: int) -> dict[str, int]:
    """Input literals for CUPL .sim / csim (idx5 decode inputs)."""
    op = opcode & 0x1F
    ph = phase & 3
    env: dict[str, int] = {name: 0 for name in CSIM_INPUT_ORDER}
    env["clk"] = 0
    for i in range(5):
        env[f"opc{i}"] = (op >> i) & 1
    env["ph0"] = ph & 1
    env["ph1"] = (ph >> 1) & 1
    return env


def golden_for_opcode_phase(opcode: int, phase: int) -> dict[str, bool]:
    """Expected LUT outputs; inactive idx5 slots are all false."""
    from simulators.cyclesim.data.fsm_table import lookup_row

    row = lookup_row(opcode, phase)
    if row is None:
        return {sig: False for sig in FSM_OUTPUT_SIGNALS}
    return row_bools(row)


def csim_input_bits(opcode: int, phase: int) -> list[int]:
    env = sim_env(opcode, phase)
    return [env[name] for name in CSIM_INPUT_ORDER]


def csim_output_chars(expected: dict[str, bool]) -> list[str]:
    return ["H" if expected[sig] else "L" for sig in FSM_OUTPUT_SIGNALS]


def format_csim_vector(
    opcode: int,
    phase: int,
    comment: str = "",
    *,
    input_order: tuple[str, ...] = CSIM_INPUT_ORDER,
) -> str:
    env = sim_env(opcode, phase)
    ins = " ".join(str(env[name]) for name in input_order)
    outs = " ".join(csim_output_chars(golden_for_opcode_phase(opcode, phase)))
    line = f"{ins}  {outs}"
    if comment:
        line += f"  /* {comment} */"
    return line


def find_inactive_idx5_lut(lut_equations: dict[str, str]) -> int:
    """idx5 slot absent from fsm_table with all LUT outputs low."""
    from simulators.cyclesim.data.fsm_table import active_idx5_slots, lookup_row

    from sim_fsm_eval import eval_ctrl_lut_signal

    active = set(active_idx5_slots())
    for idx5 in range(128):
        if idx5 in active:
            continue
        op = (idx5 >> 2) & 0x1F
        ph = idx5 & 3
        if lookup_row(op, ph) is not None:
            continue
        if all(
            not eval_ctrl_lut_signal(lut_equations, sig, op, ph)
            for sig in FSM_OUTPUT_SIGNALS
        ):
            return idx5
    raise RuntimeError("no fully-inactive idx5 slot in ctrl_lut")
