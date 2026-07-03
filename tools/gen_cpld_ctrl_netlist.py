#!/usr/bin/env python3
"""Generate CPLD control-extraction research netlists + unit catalogs."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from cpld_ctrl_model import _legacy_cw16_b_fields, build_v10_ctrl_table  # noqa: E402
from pack_control_store import FSM_OPCODE_TABLE, pack_cw16  # noqa: E402

NL_DIR = ROOT / "hw" / "netlist" / "research"
UNIT_DIR = ROOT / "hw" / "units" / "research"

TEMPLATES = ("ALU_REG", "MEM_LD", "MEM_ST", "XFER", "BEQ", "JMP", "HALT")
STROBE_OUTS = ("reg_we", "mem_rd", "mem_wr", "y_oe", "pc_load_en")


@dataclass
class UnitMeta:
    id: str
    kind: str
    label: str
    stage: int
    package_ref: str
    slot: str = ""


@dataclass
class NetlistBuild:
    block: str
    description: str
    instances: list[str] = field(default_factory=list)
    nets: set[str] = field(default_factory=set)
    units: list[UnitMeta] = field(default_factory=list)
    _gate_refs: set[str] = field(default_factory=set)
    _n04: int = 0
    _n08: int = 0
    _n32: int = 0

    def add_net(self, name: str) -> None:
        self.nets.add(name)

    def _fresh(self, prefix: str) -> str:
        n = f"net_{prefix}_{len(self.nets)}"
        self.add_net(n)
        return n

    def _new04(self) -> str:
        self._n04 += 1
        return f"U_{self.block.upper()}_04_{self._n04}"

    def _new08(self) -> str:
        self._n08 += 1
        return f"U_{self.block.upper()}_08_{self._n08}"

    def _new32(self) -> str:
        self._n32 += 1
        return f"U_{self.block.upper()}_32_{self._n32}"

    def _add(self, ref: str, part: str, pins: dict[str, str]) -> None:
        lines = [f"  - ref: {ref}", f"    part: {part}", "    pins:"]
        for k, v in pins.items():
            lines.append(f"      {k}: {v}")
            if not v.startswith("pwr_"):
                self.add_net(v)
        self.instances.append("\n".join(lines))

    def _literal_opc(self, bit: int, val: int) -> str:
        src = f"net_opc{bit}"
        self.add_net(src)
        if val == 1:
            return src
        out = self._fresh(f"nopc{bit}")
        self._add(self._new04(), "74HC04", {"A": src, "Y": out, "VCC": "pwr_vcc", "GND": "pwr_gnd"})
        return out

    def _and(self, a: str, b: str) -> str:
        if a == "pwr_gnd" or b == "pwr_gnd":
            return "pwr_gnd"
        if a == "pwr_vcc":
            return b
        if b == "pwr_vcc":
            return a
        out = self._fresh("a")
        ref = self._new08()
        self._add(ref, "74HC08", {"A": a, "B": b, "Y": out, "VCC": "pwr_vcc", "GND": "pwr_gnd"})
        if ref not in self._gate_refs:
            self._gate_refs.add(ref)
            self.register_gate(ref, kind="and_gate", label=ref, stage=2)
        return out

    def _or(self, a: str, b: str) -> str:
        if a == "pwr_gnd":
            return b
        if b == "pwr_gnd":
            return a
        out = self._fresh("o")
        ref = self._new32()
        self._add(ref, "74HC32", {"A": a, "B": b, "Y": out, "VCC": "pwr_vcc", "GND": "pwr_gnd"})
        if ref not in self._gate_refs:
            self._gate_refs.add(ref)
            self.register_gate(ref, kind="or_gate", label=ref, stage=2)
        return out

    def _or_many(self, terms: list[str]) -> str:
        live = [t for t in terms if t != "pwr_gnd"]
        if not live:
            return "pwr_gnd"
        cur = live[0]
        for t in live[1:]:
            cur = self._or(cur, t)
        return cur

    def _match_opc(self, opcode: int) -> str:
        terms = [self._literal_opc(b, (opcode >> b) & 1) for b in range(5)]
        cur = terms[0]
        for t in terms[1:]:
            cur = self._and(cur, t)
        return cur

    def _buf_to(self, src: str, dst: str) -> None:
        if src == dst:
            return
        ref = self._new08()
        self._add(
            ref,
            "74HC08",
            {"A": src, "B": "pwr_vcc", "Y": dst, "VCC": "pwr_vcc", "GND": "pwr_gnd"},
        )

    def register_gate(
        self,
        ref: str,
        *,
        kind: str,
        label: str,
        stage: int,
        unit_id: str | None = None,
        slot: str = "",
    ) -> None:
        self.units.append(
            UnitMeta(
                id=unit_id or ref.lower(),
                kind=kind,
                label=label,
                stage=stage,
                package_ref=ref,
                slot=slot,
            )
        )

    def write_netlist(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        net_lines = []
        for n in sorted(self.nets):
            if n.startswith("pwr_"):
                continue
            net_lines.append(f"  - name: {n}\n    width: 1")
        for p in ("pwr_vcc", "pwr_gnd"):
            net_lines.append(f"  - name: {p}\n    width: 1")
        text = (
            f"version: 1\nblock: {self.block}\n"
            f"description: {self.description}\ninstances:\n"
            + "\n".join(self.instances)
            + "\nnets:\n"
            + "\n".join(net_lines)
            + "\n"
        )
        path.write_text(text, encoding="utf-8")

    def write_catalog(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = ["version: 1", f"block: {self.block}", "units:"]
        for u in self.units:
            lines.append(f"  - id: {u.id}")
            lines.append(f"    kind: {u.kind}")
            lines.append(f"    label: {u.label}")
            lines.append(f"    stage: {u.stage}")
            lines.append(f"    package_ref: {u.package_ref}")
            if u.slot:
                lines.append(f"    slot: {u.slot}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _template_id(name: str) -> int:
    return TEMPLATES.index(name)


def _phase_match(nb: NetlistBuild, ph: int) -> str:
    if (ph & 1) == 0:
        inv = nb._fresh("ph0n")
        nb._add(nb._new04(), "74HC04", {"A": "net_phase0", "Y": inv, "VCC": "pwr_vcc", "GND": "pwr_gnd"})
        p0 = inv
    else:
        p0 = nb._and("net_phase0", "pwr_vcc")
    if (ph >> 1) & 1:
        p1 = nb._and("net_phase1", "pwr_vcc")
    else:
        inv1 = nb._fresh("ph1n")
        nb._add(nb._new04(), "74HC04", {"A": "net_phase1", "Y": inv1, "VCC": "pwr_vcc", "GND": "pwr_gnd"})
        p1 = inv1
    return nb._and(p0, p1)


def build_counter_netlist() -> NetlistBuild:
    nb = NetlistBuild(
        block="cpld_ctrl_counter",
        description="counter_template — 161 phase + opcode template SOP + 153 w_sel + 574 strobes",
    )
    for b in range(5):
        nb.add_net(f"net_opc{b}")
    nb.add_net("net_clk")
    nb.add_net("net_flg_z")
    nb.add_net("net_macro_end")
    nb.add_net("net_phase0")
    nb.add_net("net_phase1")
    for t in range(len(TEMPLATES)):
        nb.add_net(f"net_tpl{t}")
    for s in STROBE_OUTS:
        nb.add_net(f"net_{s}")
    nb.add_net("net_pc_load")

    ref161 = "U_PH_161"
    nb._add(
        ref161,
        "74HC161",
        {
            "CLK": "net_clk",
            "ENP": "pwr_vcc",
            "ENT": "pwr_vcc",
            "LOAD": "net_macro_end",
            "CLR": "pwr_vcc",
            "QA": "net_phase0",
            "QB": "net_phase1",
            "QC": "pwr_gnd",
            "QD": "pwr_gnd",
            "VCC": "pwr_vcc",
            "GND": "pwr_gnd",
        },
    )
    nb.register_gate(ref161, kind="counter4", label="phase 161", stage=1, unit_id="phase_161")

    ref138 = "U_OPC_138"
    nb._add(
        ref138,
        "74HC138",
        {
            "A": "net_opc0",
            "B": "net_opc1",
            "C": "net_opc2",
            "G1": "pwr_vcc",
            "G2A": "pwr_gnd",
            "G2B": "pwr_gnd",
            "Y0": "net_opc_cls0",
            "Y1": "net_opc_cls1",
            "Y2": "net_opc_cls2",
            "Y3": "net_opc_cls3",
            "Y4": "net_opc_cls4",
            "Y5": "net_opc_cls5",
            "Y6": "net_opc_cls6",
            "Y7": "net_opc_cls7",
            "VCC": "pwr_vcc",
            "GND": "pwr_gnd",
        },
    )
    nb.register_gate(ref138, kind="decoder3x8", label="opcode class 138", stage=2, unit_id="opc_138")

    tpl_minterms: dict[int, list[int]] = {i: [] for i in range(len(TEMPLATES))}
    for op, meta in FSM_OPCODE_TABLE.items():
        tpl_minterms[_template_id(meta["template"])].append(op)

    for tid, ops in tpl_minterms.items():
        dst = f"net_tpl{tid}"
        if ops:
            term = nb._or_many([nb._match_opc(op) for op in ops])
            nb._buf_to(term, dst)
        else:
            nb._buf_to("pwr_gnd", dst)

    rows = build_v10_ctrl_table()
    strobe_terms: dict[str, list[str]] = {s: [] for s in STROBE_OUTS}
    for row in rows:
        tid = _template_id(row.template)
        tpl_term = nb._and(f"net_tpl{tid}", _phase_match(nb, row.phase))
        for sig in STROBE_OUTS:
            if getattr(row, sig, 0):
                strobe_terms[sig].append(tpl_term)

    for sig in STROBE_OUTS:
        nb._buf_to(nb._or_many(strobe_terms[sig]), f"net_{sig}")

    ref153 = "U_WSEL_153"
    nb._add(
        ref153,
        "74HC153",
        {
            "1G": "pwr_gnd",
            "2G": "pwr_gnd",
            "A": "net_opc0",
            "B": "net_opc1",
            "1C0": "pwr_gnd",
            "1C1": "pwr_vcc",
            "1C2": "pwr_gnd",
            "1C3": "pwr_vcc",
            "1Y": "net_wsel0",
            "2C0": "pwr_gnd",
            "2C1": "pwr_vcc",
            "2C2": "pwr_vcc",
            "2C3": "pwr_gnd",
            "2Y": "net_wsel1",
            "VCC": "pwr_vcc",
            "GND": "pwr_gnd",
        },
    )
    nb.add_net("net_wsel0")
    nb.add_net("net_wsel1")
    nb.register_gate(ref153, kind="mux4_l", label="w_sel 153", stage=3, unit_id="wsel_153")

    ref574 = "U_CTRL_574"
    pins574: dict[str, str] = {
        "CLK": "net_clk",
        "OE": "pwr_gnd",
        "VCC": "pwr_vcc",
        "GND": "pwr_gnd",
    }
    latch_map = [
        ("D0", "net_reg_we", "Q0", "net_reg_we_lat"),
        ("D1", "net_mem_rd", "Q1", "net_mem_rd_lat"),
        ("D2", "net_mem_wr", "Q2", "net_mem_wr_lat"),
        ("D3", "net_y_oe", "Q3", "net_y_oe_lat"),
        ("D4", "net_wsel0", "Q4", "net_wsel0_lat"),
        ("D5", "net_wsel1", "Q5", "net_wsel1_lat"),
        ("D6", "net_pc_load_en", "Q6", "net_pc_load_en_lat"),
        ("D7", "pwr_gnd", "Q7", "net_rsv_lat"),
    ]
    for d, dnet, q, qnet in latch_map:
        pins574[d] = dnet
        pins574[q] = qnet
        nb.add_net(qnet)
    nb._add(ref574, "74HC574", pins574)
    nb.register_gate(ref574, kind="latch8", label="ctrl 574", stage=4, unit_id="ctrl_574")

    refbeq = "U_BEQ_AND"
    nb._add(
        refbeq,
        "74HC08",
        {
            "A": "net_pc_load_en_lat",
            "B": "net_flg_z",
            "Y": "net_pc_load",
            "VCC": "pwr_vcc",
            "GND": "pwr_gnd",
        },
    )
    nb.register_gate(refbeq, kind="and_gate", label="BEQ PC_LOAD∧Z", stage=5, unit_id="beq_and")

    return nb


def build_cw16_netlist() -> NetlistBuild:
    nb = NetlistBuild(
        block="cpld_ctrl_cw16",
        description="flash_cw16_direct — Flash CW + 574×2 + addr mux + BEQ glue",
    )
    for b in range(5):
        nb.add_net(f"net_opc{b}")
    nb.add_net("net_phase0")
    nb.add_net("net_phase1")
    nb.add_net("net_clk")
    nb.add_net("net_flg_z")
    nb.add_net("net_pc_load")
    for b in range(6):
        nb.add_net(f"net_cw_addr{b}")
    for b in range(8):
        nb.add_net(f"net_cw_lo{b}")
        nb.add_net(f"net_cw_hi{b}")
    for sig in (
        "reg_we",
        "mem_rd",
        "mem_wr",
        "y_oe",
        "cin",
        "b_sel",
        "b_const_sel",
        "y_mux_sel",
        "pc_load_en",
    ):
        nb.add_net(f"net_{sig}")
    for b in range(4):
        nb.add_net(f"net_lgc{b}")

    ref157 = "U_ADDR_157"
    nb._add(
        ref157,
        "74HC157",
        {
            "1A": "net_opc0",
            "1B": "net_phase0",
            "1Y": "net_cw_addr0",
            "2A": "net_opc1",
            "2B": "net_phase1",
            "2Y": "net_cw_addr1",
            "3A": "net_opc2",
            "3B": "pwr_gnd",
            "3Y": "net_cw_addr2",
            "4A": "net_opc3",
            "4B": "pwr_gnd",
            "4Y": "net_cw_addr3",
            "S": "pwr_gnd",
            "OE": "pwr_gnd",
            "VCC": "pwr_vcc",
            "GND": "pwr_gnd",
        },
    )
    nb.register_gate(
        ref157,
        kind="mux2_addr",
        label="CW addr 157",
        stage=1,
        unit_id="addr_157",
        slot="bit1",
    )

    refrom = "U_FLASH_CW"
    rom_pins: dict[str, str] = {"OE": "pwr_gnd", "VCC": "pwr_vcc", "GND": "pwr_gnd"}
    for b in range(6):
        rom_pins[f"A{b}"] = f"net_cw_addr{b}"
    for b in range(8):
        rom_pins[f"D{b}"] = f"net_cw_lo{b}"
        rom_pins[f"D{b + 8}"] = f"net_cw_hi{b}"
    nb._add(refrom, "FLASH_CW16", rom_pins)
    nb.register_gate(refrom, kind="rom16", label="Flash $4000 CW", stage=2, unit_id="flash_cw")

    sample = next(r for r in build_v10_ctrl_table() if r.mem_rd)
    leg_b_sel, leg_b_const = _legacy_cw16_b_fields(sample)
    _ = pack_cw16(
        reg_we=sample.reg_we,
        mem_rd=sample.mem_rd,
        mem_wr=sample.mem_wr,
        y_oe=sample.y_oe,
        cin=sample.cin,
        b_sel=leg_b_sel,
        b_const_sel=leg_b_const,
        lgc=sample.lgc0 | (sample.lgc1 << 1) | (sample.lgc2 << 2) | (sample.lgc3 << 3),
        y_mux_sel=sample.y_mux_sel,
    )

    ref574_lo = "U_LATCH_STB"
    lo_pins: dict[str, str] = {
        "CLK": "net_clk",
        "OE": "pwr_gnd",
        "VCC": "pwr_vcc",
        "GND": "pwr_gnd",
    }
    lo_map = [
        ("D0", "net_cw_lo0", "Q0", "net_reg_we"),
        ("D1", "net_cw_lo1", "Q1", "net_mem_rd"),
        ("D2", "net_cw_lo2", "Q2", "net_mem_wr"),
        ("D3", "net_cw_lo3", "Q3", "net_y_oe"),
        ("D4", "net_cw_lo4", "Q4", "net_pc_load_en"),
        ("D5", "net_cw_lo5", "Q5", "net_rsv5"),
        ("D6", "net_cw_lo6", "Q6", "net_rsv6"),
        ("D7", "net_cw_lo7", "Q7", "net_rsv7"),
    ]
    for d, dnet, q, qnet in lo_map:
        lo_pins[d] = dnet
        lo_pins[q] = qnet
        if qnet.startswith("net_"):
            nb.add_net(qnet)
    nb._add(ref574_lo, "74HC574", lo_pins)
    nb.register_gate(ref574_lo, kind="latch8", label="strobe 574", stage=3, unit_id="latch_stb")

    ref574_hi = "U_LATCH_ALU"
    hi_pins: dict[str, str] = {
        "CLK": "net_clk",
        "OE": "pwr_gnd",
        "VCC": "pwr_vcc",
        "GND": "pwr_gnd",
    }
    hi_map = [
        ("D0", "net_cw_hi0", "Q0", "net_cin"),
        ("D1", "net_cw_hi1", "Q1", "net_b_sel"),
        ("D2", "net_cw_hi2", "Q2", "net_b_const_sel"),
        ("D3", "net_cw_hi3", "Q3", "net_y_mux_sel"),
        ("D4", "net_cw_hi4", "Q4", "net_lgc0"),
        ("D5", "net_cw_hi5", "Q5", "net_lgc1"),
        ("D6", "net_cw_hi6", "Q6", "net_lgc2"),
        ("D7", "net_cw_hi7", "Q7", "net_lgc3"),
    ]
    for d, dnet, q, qnet in hi_map:
        hi_pins[d] = dnet
        hi_pins[q] = qnet
    nb._add(ref574_hi, "74HC574", hi_pins)
    nb.register_gate(ref574_hi, kind="latch8", label="ALU cw 574", stage=3, unit_id="latch_alu")

    refbeq = "U_BEQ_AND"
    nb._add(
        refbeq,
        "74HC08",
        {
            "A": "net_pc_load_en",
            "B": "net_flg_z",
            "Y": "net_pc_load",
            "VCC": "pwr_vcc",
            "GND": "pwr_gnd",
        },
    )
    nb.register_gate(refbeq, kind="and_gate", label="BEQ PC_LOAD∧Z", stage=4, unit_id="beq_and")

    return nb


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate CPLD control research netlists")
    ap.add_argument(
        "--arch",
        choices=("counter_template", "flash_cw16_direct", "all"),
        default="all",
    )
    args = ap.parse_args()

    builds: list[tuple[str, NetlistBuild]] = []
    if args.arch in ("counter_template", "all"):
        builds.append(("cpld_ctrl_counter", build_counter_netlist()))
    if args.arch in ("flash_cw16_direct", "all"):
        builds.append(("cpld_ctrl_cw16", build_cw16_netlist()))

    for name, nb in builds:
        nl_path = NL_DIR / f"{name}.yaml"
        cat_path = UNIT_DIR / f"{name}.yaml"
        nb.write_netlist(nl_path)
        nb.write_catalog(cat_path)
        print(f"wrote {nl_path} ({len(nb.instances)} inst, {len(nb.units)} units)")
        print(f"wrote {cat_path}")


if __name__ == "__main__":
    main()
