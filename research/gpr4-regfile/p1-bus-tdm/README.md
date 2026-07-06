# P1 — Single-bus time-division multiplexing + clock division

**Status:** Research (non-normative)  
**Date:** 2026-07-07  
**Parent:** [../README.md](../README.md) · Prior pin study: [../pin-budget.md](../pin-budget.md)

Studies **P1-bus-TDM**: merge `q_a`/`q_b` into **`q_bus[7:0]`**, time-multiplex operand A/B at **4 MHz micro-phases** within one **2 MHz** execute half-cycle (250 ns), latch A in external **74HC574**, and add full **4-GPR** `r_sel_a`/`r_sel_b` while staying within **ATF1504AS-10JU44** 32 user I/O.

---

## Executive summary

| Gate | Result |
|------|--------|
| **Pins (desk)** | **PASS** — DP **28/32** (C0, no clk export) |
| **MC (desk)** | **LIKELY PASS** — ~48–58 MC on DP (4:1 mux + u_phase + R3) |
| **Timing (desk)** | **CONDITIONAL** — ADD marginal / INC **FAIL** in single 250 ns window without **M1–M4** mitigation |
| **BOM** | **+1× 574** (ALU A latch); clock option may remove **74HC74** (C1/C2) |

**Conclusion:** P1 **solves the P0 pin overrun** via bus merge; **timing is the new binding constraint** for arithmetic execute in one macro half-cycle.

---

## Documents

| File | Content |
|------|---------|
| **[SUMMARY-REPORT.md](SUMMARY-REPORT.md)** | **P1 연구만 요약한 별도 리포트** |
| **[REPORT.md](REPORT.md)** | 상세 종합 (지시서 대응) |
| [clock-topologies.md](clock-topologies.md) | C0–C4 clock distribution options |
| [pin-map.md](pin-map.md) | PLCC-44 I/O declaration list |
| [timing-cross-domain.md](timing-cross-domain.md) | T1/T2 setup/hold, critical path, M1–M4 |
| [../variants/p1_dp_bus_tdm/](../variants/p1_dp_bus_tdm/) | DP WinCUPL skeleton |
| [../variants/p1_cu_clkgen/](../variants/p1_cu_clkgen/) | CU clockgen skeleton (C1) |

---

## Architecture sketch

```text
  4 MHz OSC ──► CPLD-DP (clk_4m)     CU idx5 FSM @ clk_2m
                    │                      │
                    │ G-IC r_sel_a/b       │
                    ▼                      │
              q_bus[7:0] ──► 574 (A latch) ──► ALU A
                    └──────────────────────────► ALU B (direct, T2)
```

Micro-sequence per 250 ns execute half (one 4 MHz period):

| Window | Action |
|--------|--------|
| T1 0–125 ns | `r_sel_a` → `q_bus`; `alu_a_le` pulse → capture A |
| T2 125–250 ns | `r_sel_b` → `q_bus` → ALU B; ALU comb settles |
| T3 @ 250 ns | `clk_2m` ↑ — FSM phase advance, GPR writes |

---

## Open items

- [ ] WinCUPL fit on DP/CU skeletons (local)
- [ ] Pick clock topology (C0 vs C1) after timing mitigation choice
- [ ] Breadboard scope: `q_bus`, `alu_a_le`, 574 A vs `net_clk2`
