"""Generate regfile+ALU RMW slack netlists and hwsim tests (8 vs 4 reg MUX topologies)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALU_B3 = ROOT / "hw" / "netlist" / "blocks" / "alu_b3.yaml"
BLOCKS = ROOT / "hw" / "netlist" / "blocks"
TESTS = ROOT / "hw" / "tests"

# Measured SUB B critical path inside alu_b3 (hwsim max, ns).
ALU_SUB_SUFFIX = [
    "U_ALU_86_INV_0.A",
    "U_ALU_86_INV_0.Y",
    "U_ALU_157_B_0.1B",
    "U_ALU_157_B_0.1Y",
    "U_ALU_157_B2_0.1A",
    "U_ALU_157_B2_0.1Y",
    "U_ALU_283_LO.B0",
    "U_ALU_283_LO.C4",
    "U_ALU_283_HI.C4",
    "U_ALU_153_0.1C0",
    "U_ALU_153_0.1Y",
]

BUDGET_NS = 250
MARGIN_NS = 15

TOPOLOGIES: dict[str, dict] = {
    "regfile_rmw_8x151": {
        "block": "regfile_rmw_8x151",
        "reg_count": 8,
        "mux_ic_per_port": 8,
        "mux_ic_total": 16,
        "574_count": 8,
        "instances": """
  - ref: U_REG_DST
    part: 74HC574
    pins:
      D0: net_y0
      D1: net_y1
      D2: net_y2
      D3: net_y3
      D4: net_y4
      D5: net_y5
      D6: net_y6
      D7: net_y7
      Q0: net_reg_q0
      Q1: net_reg_q1
      Q2: net_reg_q2
      Q3: net_reg_q3
      Q4: net_reg_q4
      Q5: net_reg_q5
      Q6: net_reg_q6
      Q7: net_reg_q7
      CP: net_clk
      OE: pwr_gnd
      VCC: pwr_vcc
      GND: pwr_gnd
  - ref: U_MUX_B0
    part: 74HC151
    pins:
      D0: net_reg_q0
      D1: net_reg_q1
      D2: net_reg_q2
      D3: net_reg_q3
      D4: net_reg_q4
      D5: net_reg_q5
      D6: net_reg_q6
      D7: net_reg_q7
      S0: net_mux_s0
      S1: net_mux_s1
      S2: net_mux_s2
      W: pwr_gnd
      Y: net_b0
      VCC: pwr_vcc
      GND: pwr_gnd
""",
        "extra_nets": """
  - name: net_reg_q0
    width: 1
  - name: net_reg_q1
    width: 1
  - name: net_reg_q2
    width: 1
  - name: net_reg_q3
    width: 1
  - name: net_reg_q4
    width: 1
  - name: net_reg_q5
    width: 1
  - name: net_reg_q6
    width: 1
  - name: net_reg_q7
    width: 1
  - name: net_mux_s0
    width: 1
  - name: net_mux_s1
    width: 1
  - name: net_mux_s2
    width: 1
""",
        "slack_path": ["U_REG_DST.Q0", "U_MUX_B0.Y"] + ALU_SUB_SUFFIX,
        "stimulus_mux": {"net_mux_s0": 1, "net_mux_s1": 0, "net_mux_s2": 1},
    },
    "regfile_rmw_4x153": {
        "block": "regfile_rmw_4x153",
        "reg_count": 4,
        "mux_ic_per_port": 4,
        "mux_ic_total": 8,
        "574_count": 4,
        "instances": """
  - ref: U_REG_DST
    part: 74HC574
    pins:
      D0: net_y0
      D1: net_y1
      D2: net_y2
      D3: net_y3
      D4: net_y4
      D5: net_y5
      D6: net_y6
      D7: net_y7
      Q0: net_reg_q0
      Q1: net_reg_q1
      Q2: net_reg_q2
      Q3: net_reg_q3
      CP: net_clk
      OE: pwr_gnd
      VCC: pwr_vcc
      GND: pwr_gnd
  - ref: U_MUX_B0
    part: 74HC153
    pins:
      1C0: net_reg_q0
      1C1: net_reg_q1
      1C2: net_reg_q2
      1C3: net_reg_q3
      1G: pwr_gnd
      A: net_mux_s0
      B: net_mux_s1
      1Y: net_b0
      2G: pwr_vcc
      VCC: pwr_vcc
      GND: pwr_gnd
""",
        "extra_nets": """
  - name: net_reg_q0
    width: 1
  - name: net_reg_q1
    width: 1
  - name: net_reg_q2
    width: 1
  - name: net_reg_q3
    width: 1
  - name: net_mux_s0
    width: 1
  - name: net_mux_s1
    width: 1
""",
        "slack_path": ["U_REG_DST.Q0", "U_MUX_B0.1Y"] + ALU_SUB_SUFFIX,
        "stimulus_mux": {"net_mux_s0": 0, "net_mux_s1": 0},
    },
    "regfile_rmw_8x153157": {
        "block": "regfile_rmw_8x153157",
        "reg_count": 8,
        "mux_ic_per_port": 12,
        "mux_ic_total": 24,
        "574_count": 8,
        "instances": """
  - ref: U_REG_DST
    part: 74HC574
    pins:
      D0: net_y0
      D1: net_y1
      D2: net_y2
      D3: net_y3
      D4: net_y4
      D5: net_y5
      D6: net_y6
      D7: net_y7
      Q0: net_reg_q0
      Q1: net_reg_q1
      Q2: net_reg_q2
      Q3: net_reg_q3
      Q4: net_reg_q4
      Q5: net_reg_q5
      Q6: net_reg_q6
      Q7: net_reg_q7
      CP: net_clk
      OE: pwr_gnd
      VCC: pwr_vcc
      GND: pwr_gnd
  - ref: U_MUX153_LO
    part: 74HC153
    pins:
      1C0: net_reg_q0
      1C1: net_reg_q1
      1C2: net_reg_q2
      1C3: net_reg_q3
      1G: pwr_gnd
      A: net_mux_s0
      B: net_mux_s1
      1Y: net_mux_mid
      2G: pwr_vcc
      VCC: pwr_vcc
      GND: pwr_gnd
  - ref: U_MUX157_HI
    part: 74HC157
    pins:
      1A: net_mux_mid
      1B: net_reg_q4
      1Y: net_b0
      S: net_mux_s2
      OE: pwr_gnd
      VCC: pwr_vcc
      GND: pwr_gnd
""",
        "extra_nets": """
  - name: net_reg_q0
    width: 1
  - name: net_reg_q1
    width: 1
  - name: net_reg_q2
    width: 1
  - name: net_reg_q3
    width: 1
  - name: net_reg_q4
    width: 1
  - name: net_reg_q5
    width: 1
  - name: net_reg_q6
    width: 1
  - name: net_reg_q7
    width: 1
  - name: net_mux_mid
    width: 1
  - name: net_mux_s0
    width: 1
  - name: net_mux_s1
    width: 1
  - name: net_mux_s2
    width: 1
""",
        "slack_path": [
            "U_REG_DST.Q0",
            "U_MUX153_LO.1Y",
            "U_MUX157_HI.1Y",
        ]
        + ALU_SUB_SUFFIX,
        "stimulus_mux": {"net_mux_s0": 0, "net_mux_s1": 0, "net_mux_s2": 0},
    },
}


def _write_netlist(name: str, topo: dict) -> None:
    text = ALU_B3.read_text(encoding="utf-8")
    text = text.replace("block: alu_b3", f"block: {topo['block']}", 1)

    drop = "  - ref: U_REG_574_ACC"
    idx = text.find(drop)
    if idx >= 0:
        end = text.find("\nnets:", idx)
        if end >= 0:
            text = text[:idx] + text[end:]

    marker = "\nnets:"
    head, tail = text.split(marker, 1)
    head = head.rstrip() + topo["instances"].rstrip() + "\n"
    extra = topo["extra_nets"].lstrip("\n").rstrip()
    out = head + "nets:\n" + extra + "\n" + tail.lstrip("\n")
    (BLOCKS / f"{name}.yaml").write_text(out, encoding="utf-8")


def _write_test(name: str, topo: dict) -> None:
    mux = topo["stimulus_mux"]
    path_comb = ", ".join(topo["slack_path"])
    path_setup = topo["slack_path"] + ["U_REG_DST.D0", "U_REG_DST.CP"]
    path_e2e = ", ".join(path_setup)
    stim = {
        "net_a0": 0,
        "net_a1": 1,
        "net_a2": 0,
        "net_a3": 0,
        "net_a4": 1,
        "net_a5": 0,
        "net_a6": 0,
        "net_a7": 0,
        "net_b1": 0,
        "net_b2": 1,
        "net_b3": 0,
        "net_b4": 1,
        "net_b5": 1,
        "net_b6": 0,
        "net_b7": 0,
        "net_sub_en": 1,
        "net_cin": 1,
        "net_153_s0": 0,
        "net_153_s1": 0,
        "net_b_sel": 1,
        "net_b_const_sel": 0,
        "net_c3_sel": 0,
        "net_b_const_bit1": 0,
        "net_b_const_bit2": 0,
        "net_b_const_bit3": 0,
        "net_b_const_bit4": 0,
        "net_b_const_bit5": 0,
        "net_b_const_bit6": 0,
        "net_b_const_bit7": 0,
        "net_clk": 0,
        **mux,
    }
    stim_lines = "\n".join(f"      {k}: {v}" for k, v in stim.items())
    body = f"""netlist: ../netlist/blocks/{name}.yaml
timing: max
duration_ns: 500
stimulus:
  - at_ns: 0
    set:
{stim_lines}
checks:
  - type: slack
    path: [{path_comb}]
    budget_ns: {BUDGET_NS}
    min_slack_ns: 0
  - type: slack
    path: [{path_e2e}]
    budget_ns: {BUDGET_NS}
    min_slack_ns: 0
"""
    (TESTS / f"{name}_slack.yaml").write_text(body, encoding="utf-8")


def main() -> None:
    for name, topo in TOPOLOGIES.items():
        _write_netlist(name, topo)
        _write_test(name, topo)
        print(f"wrote {name}.yaml + {name}_slack.yaml")


if __name__ == "__main__":
    main()
