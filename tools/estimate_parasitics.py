#!/usr/bin/env python3
"""
Breadboard parasitic inductance / capacitance estimator for Plover CPU variants.

First-order model for comparing architecture trade-offs (IC count vs wire hops).
Not a substitute for scope measurement — constants are documented below.

Usage:
  python tools/estimate_parasitics.py
  python tools/estimate_parasitics.py --json
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass, field


# --- Physical constants (breadboard + 74HC DIP @ 5 V) -------------------------
# Sources: rule-of-thumb 8–15 nH/cm for loose wire; contact ~1–3 nH;
#          74HC C_in ~5 pF (datasheet); I_out ~±24 mA; edge ~3–8 ns @ 5 V.

NH_PER_CM = 10.0  # nH/cm signal + return loop (single-ended estimate)
NH_PER_CONTACT = 2.0  # nH per breadboard spring / header pin
CM_PER_CHIP_HOP = 2.5  # avg jumper length when ICs are adjacent on MB-102
NH_PLCC_PIN = 8.0  # extra vs DIP: adapter socket + longer lead
NH_SOIC_BREAKOUT = 12.0  # LVC245 / SRAM adapter penalty per pin

PF_PER_74HC_INPUT = 5.0
PF_BREADBOARD_STUB = 3.0  # per node (strip + hop)

I_SWITCH_MA = 20.0  # per output bit, typical HC @ 5 V
T_RISE_NS = 6.0  # conservative breadboard edge (not datasheet min)
F_CLK_MHZ = 2.0


@dataclass
class NetModel:
    """One logical net or parallel bus (all bits switch together)."""

    name: str
    width: int
    hops: int  # chip-to-chip segments per bit (one-way)
    contacts: int  # breadboard touches per bit
    fanout: int  # loads driven simultaneously
    adapter_nh: float = 0.0  # extra L per bit (PLCC/SOIC)
    extra_pf: float = 0.0  # beyond fanout * C_in

    def L_bit_nH(self) -> float:
        wire = self.hops * CM_PER_CHIP_HOP * NH_PER_CM
        touch = self.contacts * NH_PER_CONTACT
        # Fan-out branches add parallel stub inductance (approx upper bound).
        branch = 0.35 * self.fanout * (CM_PER_CHIP_HOP * NH_PER_CM + 2 * NH_PER_CONTACT)
        return wire + touch + branch + self.adapter_nh

    def C_bit_pF(self) -> float:
        return self.fanout * PF_PER_74HC_INPUT + PF_BREADBOARD_STUB + self.extra_pf

    def L_bus_nH(self) -> float:
        """Effective loop L when width bits switch together (shared return)."""
        # Shared power/ground path: not fully parallel; use sqrt(width) scaling.
        scale = math.sqrt(self.width)
        return self.L_bit_nH() * scale

    def C_bus_pF(self) -> float:
        return self.C_bit_pF() * self.width

    def V_bounce_mV(self) -> float:
        """Upper-bound SSO index (mV-scale): one octal driver, L_bus, all bits edge together."""
        n = min(self.width, 8)
        i_total = n * I_SWITCH_MA * 1e-3
        di_dt = i_total / (T_RISE_NS * 1e-9)
        L = self.L_bus_nH() * 1e-9
        return L * di_dt * 1e3

    def ring_MHz(self) -> float:
        L = self.L_bus_nH() * 1e-9
        C = self.C_bus_pF() * 1e-12
        if L <= 0 or C <= 0:
            return 0.0
        return 1.0 / (2 * math.pi * math.sqrt(L * C)) / 1e6


@dataclass
class ArchVariant:
    key: str
    label: str
    dip_74hc: int
    cpld: int
    gal: int
    smd_adapters: int  # SOIC/PLCC breakout boards used
    notes: str
    nets: list[NetModel] = field(default_factory=list)

    def score_wire_hops(self) -> int:
        return sum(n.hops * n.width for n in self.nets)

    def score_contacts(self) -> int:
        return sum(n.contacts * n.width for n in self.nets)

    def L_sum_nH(self) -> float:
        return sum(n.L_bus_nH() for n in self.nets)

    def worst_v_bounce_mV(self) -> float:
        data = [n for n in self.nets if n.width >= 8 and "CLK" not in n.name]
        pool = data or self.nets
        return max((n.V_bounce_mV() for n in pool), default=0.0)

    def worst_ring_MHz(self) -> float:
        data = [n for n in self.nets if n.width >= 8 and "CLK" not in n.name]
        pool = data or self.nets
        return max((n.ring_MHz() for n in pool), default=0.0)


def build_variants() -> list[ArchVariant]:
    """Architecture presets aligned with Plover docs / purchase history."""

    # --- A: v0.1 normative — 574×4 GPR, CPLD decode only, alu8 on breadboard ---
    v01_gpr = ArchVariant(
        key="v0.1_574_gpr",
        label="v0.1 Tier 0 legacy (574×4 GPR + CPLD decode)",
        dip_74hc=34,
        cpld=1,
        gal=0,
        smd_adapters=6,  # 2 SRAM + 1 Flash + 3 LVC245
        notes="Tier 0 bring-up; archived system-architecture-v0.1.",
        nets=[
            NetModel("GPR.Q → ALU.A", 8, hops=2, contacts=6, fanout=1),
            NetModel("GPR.Q → ALU.B (via decode path)", 8, hops=3, contacts=8, fanout=1),
            NetModel("ALU.Y → GPR.D / bus", 8, hops=2, contacts=6, fanout=2),
            NetModel("ADDR[15:0]", 16, hops=3, contacts=8, fanout=3),
            NetModel("DATA bus", 8, hops=3, contacts=8, fanout=4, extra_pf=10),
            NetModel("CW[7:0] (Flash→latch)", 8, hops=2, contacts=6, fanout=3,
                     adapter_nh=NH_SOIC_BREAKOUT),
            NetModel("LOAD_R[3:0]", 4, hops=2, contacts=5, fanout=4,
                     adapter_nh=NH_PLCC_PIN),
            NetModel("cin / b_sel (ALU ctrl)", 2, hops=2, contacts=5, fanout=8),
            NetModel("CLK 2MHz", 1, hops=4, contacts=10, fanout=12),
        ],
    )

    # --- B: CPLD GPR hybrid (v1.3 — superseded but best for wire reduction) ---
    cpld_gpr = ArchVariant(
        key="v1.3_cpld_gpr",
        label="v1.3 CPLD GPR (internal R0–R3)",
        dip_74hc=28,  # −574×4, −157/153 regfile mux vs discrete GPR
        cpld=1,
        gal=0,
        smd_adapters=6,
        notes="GPR bus hidden in CPLD die; only q_a/q_b exit to ALU.",
        nets=[
            NetModel("CPLD q_a → ALU.A", 8, hops=1, contacts=4, fanout=1,
                     adapter_nh=NH_PLCC_PIN),
            NetModel("CPLD q_b → ALU.B", 8, hops=1, contacts=4, fanout=1,
                     adapter_nh=NH_PLCC_PIN),
            NetModel("ALU.Y → bus", 8, hops=2, contacts=6, fanout=2),
            NetModel("ADDR[15:0]", 16, hops=3, contacts=8, fanout=3),
            NetModel("DATA bus", 8, hops=3, contacts=8, fanout=4, extra_pf=10),
            NetModel("CW[7:0]", 8, hops=2, contacts=6, fanout=3,
                     adapter_nh=NH_SOIC_BREAKOUT),
            NetModel("LOAD_R* (unused / tie-off)", 4, hops=0, contacts=0, fanout=0),
            NetModel("cin / b_sel", 2, hops=2, contacts=5, fanout=8),
            NetModel("CLK 2MHz", 1, hops=4, contacts=10, fanout=10),
        ],
    )

    # --- C: ACC+TMP v1.2 ---
    acc_tmp = ArchVariant(
        key="v1.2_acc_tmp",
        label="v1.2 ACC+TMP (574×2, 157×4 B-mux)",
        dip_74hc=30,
        cpld=1,
        gal=0,
        smd_adapters=6,
        notes="Fewer GPR wires than 4×574; 157 B-path still on breadboard.",
        nets=[
            NetModel("ACC.Q → ALU.A (direct)", 8, hops=1, contacts=4, fanout=1),
            NetModel("157 → ALU.B", 8, hops=2, contacts=6, fanout=2),
            NetModel("ALU.Y → ACC.D", 8, hops=1, contacts=4, fanout=1),
            NetModel("ADDR[15:0]", 16, hops=3, contacts=8, fanout=3),
            NetModel("DATA bus", 8, hops=3, contacts=8, fanout=3, extra_pf=8),
            NetModel("CW[7:0]", 8, hops=2, contacts=6, fanout=3,
                     adapter_nh=NH_SOIC_BREAKOUT),
            NetModel("LOAD_R*", 2, hops=2, contacts=5, fanout=2, adapter_nh=NH_PLCC_PIN),
            NetModel("cin / b_sel", 2, hops=2, contacts=5, fanout=8),
            NetModel("CLK 2MHz", 1, hops=4, contacts=10, fanout=10),
        ],
    )

    # --- D: ACC-only v1.1 ---
    acc_only = ArchVariant(
        key="v1.1_acc",
        label="v1.1 ACC-only (574×1)",
        dip_74hc=26,
        cpld=1,
        gal=0,
        smd_adapters=6,
        notes="Minimum TTL register wiring; highest MEM traffic.",
        nets=[
            NetModel("ACC.Q → ALU.A", 8, hops=1, contacts=4, fanout=1),
            NetModel("SRAM → ALU.B", 8, hops=2, contacts=6, fanout=2,
                     adapter_nh=NH_SOIC_BREAKOUT),
            NetModel("ALU.Y → ACC.D", 8, hops=1, contacts=4, fanout=1),
            NetModel("ADDR[15:0]", 16, hops=3, contacts=8, fanout=3),
            NetModel("DATA bus", 8, hops=3, contacts=8, fanout=3, extra_pf=8),
            NetModel("CW[7:0]", 8, hops=2, contacts=6, fanout=3,
                     adapter_nh=NH_SOIC_BREAKOUT),
            NetModel("LOAD_R0", 1, hops=2, contacts=5, fanout=1, adapter_nh=NH_PLCC_PIN),
            NetModel("cin / b_sel", 2, hops=2, contacts=5, fanout=8),
            NetModel("CLK 2MHz", 1, hops=4, contacts=10, fanout=8),
        ],
    )

    # --- E: v0.1 + GAL CE/flag offload (Gemini-style) ---
    gpr_gal = ArchVariant(
        key="v0.1_gpr_gal",
        label="v0.1 GPR + ATF16V8B (CE/flags offload)",
        dip_74hc=35,
        cpld=1,
        gal=1,
        smd_adapters=6,
        notes="+1 DIP; shorter CPLD stub nets; GPR path unchanged.",
        nets=list(v01_gpr.nets),  # copy GPR nets
    )
    # Shorter CPLD control stubs (CE moved to GAL)
    gpr_gal.nets = [n for n in gpr_gal.nets if n.name not in ("LOAD_R[3:0]",)]
    gpr_gal.nets.extend([
        NetModel("LOAD_R[3:0]", 4, hops=1, contacts=3, fanout=4, adapter_nh=NH_PLCC_PIN),
        NetModel("RAM/ROM CE (GAL)", 4, hops=2, contacts=5, fanout=2),
    ])

    # --- F: v0.1 + 74HC138 for CE (already purchased) ---
    gpr_138 = ArchVariant(
        key="v0.1_gpr_138",
        label="v0.1 GPR + 74HC138 CE decode",
        dip_74hc=35,
        cpld=1,
        gal=0,
        smd_adapters=6,
        notes="+1 DIP 138; frees CPLD I/O; CE tree shorter than CPLD fanout.",
        nets=list(v01_gpr.nets),
    )
    gpr_138.nets = [n for n in gpr_138.nets if "ADDR" not in n.name]
    gpr_138.nets.append(
        NetModel("ADDR[15:0]", 16, hops=2, contacts=6, fanout=2),
    )
    gpr_138.nets.append(
        NetModel("138 Y* → RAM/ROM CE", 3, hops=1, contacts=4, fanout=2),
    )

    # --- G: v1.0 breadboard (normative) ---
    v1_breadboard = ArchVariant(
        key="v1_breadboard",
        label="v1.0 breadboard (CPLD GPR + 138×2 + 10b CW)",
        dip_74hc=31,
        cpld=1,
        gal=0,
        smd_adapters=6,
        notes="Normative; 574×5 seq+CW+FLG; 138×2 CE; REG_SEL in CW_H.",
        nets=[
            NetModel("CPLD q_a → ALU.A", 8, hops=1, contacts=4, fanout=1,
                     adapter_nh=NH_PLCC_PIN),
            NetModel("CPLD q_b → ALU.B", 8, hops=1, contacts=4, fanout=1,
                     adapter_nh=NH_PLCC_PIN),
            NetModel("ALU.Y → bus", 8, hops=2, contacts=6, fanout=2),
            NetModel("ADDR[15:0]", 16, hops=2, contacts=6, fanout=2),
            NetModel("DATA bus", 8, hops=3, contacts=8, fanout=4, extra_pf=10),
            NetModel("CW_L[7:0] + CW_H[1:0]", 10, hops=2, contacts=6, fanout=3,
                     adapter_nh=NH_SOIC_BREAKOUT),
            NetModel("138×2 Y* → /CE glue", 3, hops=1, contacts=4, fanout=2),
            NetModel("FLG 574 (Z/C)", 2, hops=2, contacts=4, fanout=2),
            NetModel("BEQ glue 08/32", 1, hops=2, contacts=4, fanout=1),
            NetModel("cin / b_sel", 2, hops=2, contacts=5, fanout=8),
            NetModel("CLK 2MHz", 1, hops=4, contacts=10, fanout=10),
        ],
    )

    gpr_gal.notes += " [REJECTED — do not buy]"
    v01_gpr.notes += " [archived Tier 0 — hw/tests/archive/tier0]"

    return [v1_breadboard, v01_gpr, cpld_gpr, acc_tmp, acc_only, gpr_gal, gpr_138]


def rank_table(variants: list[ArchVariant]) -> list[dict]:
    baseline = next(v for v in variants if v.key == "v0.1_574_gpr")
    b_hops = baseline.score_wire_hops()
    b_cont = baseline.score_contacts()
    b_L = baseline.L_sum_nH()
    b_v = baseline.worst_v_bounce_mV()

    rows = []
    for v in variants:
        rows.append({
            "key": v.key,
            "label": v.label,
            "dip_74hc": v.dip_74hc,
            "cpld": v.cpld,
            "gal": v.gal,
            "wire_hops": v.score_wire_hops(),
            "contacts": v.score_contacts(),
            "hops_vs_baseline_pct": round(100 * (1 - v.score_wire_hops() / b_hops), 1),
            "contacts_vs_baseline_pct": round(100 * (1 - v.score_contacts() / b_cont), 1),
            "L_sum_nH": round(v.L_sum_nH(), 0),
            "L_sum_vs_baseline_pct": round(100 * (1 - v.L_sum_nH() / baseline.L_sum_nH()), 1),
            "sso_index_mV": round(v.worst_v_bounce_mV(), 0),
            "sso_vs_baseline_pct": round(100 * (1 - v.worst_v_bounce_mV() / b_v), 1)
            if b_v else 0,
            "worst_ring_MHz": round(v.worst_ring_MHz(), 0),
            "notes": v.notes,
        })
    rows.sort(key=lambda r: (r["wire_hops"], r["dip_74hc"]))
    return rows


def net_detail(variant: ArchVariant) -> list[dict]:
    out = []
    for n in variant.nets:
        out.append({
            "net": n.name,
            "width": n.width,
            "L_bit_nH": round(n.L_bit_nH(), 1),
            "L_bus_nH": round(n.L_bus_nH(), 1),
            "C_bus_pF": round(n.C_bus_pF(), 0),
            "V_bounce_mV": round(n.V_bounce_mV(), 1),
            "ring_MHz": round(n.ring_MHz(), 0),
        })
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Plover breadboard parasitic estimator")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--detail", metavar="KEY", help="Net breakdown for variant key")
    args = parser.parse_args()

    variants = build_variants()

    if args.detail:
        v = next((x for x in variants if x.key == args.detail), None)
        if not v:
            raise SystemExit(f"Unknown key: {args.detail}")
        print(json.dumps(net_detail(v), indent=2))
        return

    rows = rank_table(variants)
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return

    print("Plover breadboard parasitics - first-order comparison")
    print(f"Constants: {NH_PER_CM} nH/cm, {NH_PER_CONTACT} nH/contact, "
          f"{CM_PER_CHIP_HOP} cm/hop, edge {T_RISE_NS} ns, {F_CLK_MHZ} MHz")
    print("(SSO index = upper-bound relative metric, not measured mV)")
    print()
    hdr = (
        f"{'variant':<28} {'DIP':>4} {'hops':>5} {'dHops':>6} "
        f"{'Lsum':>6} {'dL%':>5} {'SSO':>6} {'ring':>5}"
    )
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        print(
            f"{r['key']:<28} {r['dip_74hc']:>4} {r['wire_hops']:>5} "
            f"{r['hops_vs_baseline_pct']:>5.1f}% "
            f"{r['L_sum_nH']:>6.0f} {r['L_sum_vs_baseline_pct']:>4.1f}% "
            f"{r['sso_index_mV']:>6.0f} {r['worst_ring_MHz']:>5.0f}"
        )
    print()
    print("Detail: python tools/estimate_parasitics.py --detail v1_breadboard")
    print("Baseline = v0.1_574_gpr (archived Tier 0)")


if __name__ == "__main__":
    main()
