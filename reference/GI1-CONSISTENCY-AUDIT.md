# Gi1 v1.0 consistency audit

**Date:** 2026-07-07  
**Status:** Pre-migration gap report (rev G → Gi1 normative)  
**Superseded by:** Gi1 adoption commits; archive [rev-g-normative-snapshot](../archive/rev-g-normative-snapshot/)

---

## Summary

| Tier | Must edit | Archive only | No change |
|------|----------:|-------------:|----------:|
| Whitepaper | 1 | 0 | 0 |
| reference/hardware | 7 | 0 | 8 |
| reference/hw-bringup | 6 | 0 | 10 |
| reference/software | 2 | 0 | 14 |
| reference/fixtures | 1 | 0 | 3 |
| Machine (cyclesim) | 8 | 0 | — |
| research/gpr4-regfile | 3 | 1 | rest |

---

## A. Root — `plover-whitepaper.md`

| Section | rev G conflict | Action |
|---------|----------------|--------|
| §2.4 | 3-address ACC, R0,R1→R2 | **Must edit** — AC + RAM variables |
| §3.1–3.2 | R0–R2, G-IC 6, q_a/q_b | **Must edit** |
| §5.2 | cpld_3fixed R0/R1/R2 | **Must edit** — cpld_ac_mbr |
| §6.1 | TFR opcodes, ADD→R2 | **Must edit** |
| §6.2 | tfr_valid comb | **Must edit** |
| §7.3 | TFR20 asm example | **Must edit** |

---

## B. Hardware

| File | Hits | Action |
|------|------|--------|
| microcode-spec.md | TFR, R1/R2, w_sel, XFER | **Must edit** (anchor) |
| cpld-system-controller.md | rev G, TFR, q_b, G-IC 6 | **Must edit** (anchor) |
| system-architecture.md | 3-GPR, TFR, rev G metrics | **Must edit** (anchor) |
| control-and-decode.md | TFR, q_a/q_b, G-IC 6 | **Must edit** |
| cpld-dual-routing.md | q_b, G-IC 6 | **Must edit** |
| cpld-dual-timing.md | TFR latch 40 ns | **Must edit** |
| alu-opcodes-timing.md | q_b path, rev G paths | **Must edit** |
| cpld-dual-jtag.md | rev G label | **No change** (chain same) |
| memory-map.md | — | **No change** |
| rom-architecture.md | — | **No change** |
| alu8-phase-b.md | bench opcodes | **No change** |
| hw-schematic.md | — | **No change** |
| fpga-target-guide.md | — | **No change** |

---

## C. Bring-up

| File | Action |
|------|--------|
| M2b-gpr-datapath.md | **Must edit** — Gi1 G0–G4, no R1/R2 |
| M2a-cpld-decode.md | **Must edit** — drop TFR smoke |
| M3a-control-store.md | **Must edit** — idx5 row semantics |
| M3b-fetch-execute.md | **Must edit** — ADD/CMP Gi1, MBR hold |
| breadboard-wiring.md | **Must edit** — MBR→B, G-IC 1 |
| README.md | **Must edit** — Gi1 wording |
| M1-*, M2b-memory, M4*, M5 | **No change** (ALU/mem/boot) |

---

## D. Software

| File | Action |
|------|--------|
| calling-convention-v0.1.md | **Must edit** — R0 only hardware |
| compiler-isa-audit-v1.0.md | **Must edit** — GPR/TFR rows |
| plover-asm.md | **No change** |
| Others | **No change** |

---

## E. Fixtures / BOM

| File | Action |
|------|--------|
| add_imm-sram.md | **Must edit** — Gi1 interpretation |
| BOM.md | **No change** (574×3 same) |

---

## F. Machine tier

| Artifact | Action |
|----------|--------|
| fsm_table.py | **Must edit** |
| dp.py, gic.py, cu.py | **Must edit** |
| isa.py | **Must edit** |
| test_cpu_m3b.py, rom_builder.py | **Must edit** |
| test_cpld_dual.py, test_fsm_idx5.py | **Must edit** |

---

## G. Meta

| File | Action |
|------|--------|
| reference/README.md | **Must edit** |
| AGENTS.md | **Must edit** |

---

## H. Research

| Path | Action |
|------|--------|
| gi1-ac-mbr/ | **Must edit** — absorbed status |
| baseline-rev-g.md | **Archive pointer** |
| feasibility-matrix.md | **Must edit** — adopted |
| P1/P1M1 | **No change** (historical) |

---

## Truth cascade diff (opcode×phase)

| Opcode | rev G ph1 | Gi1 ph1 | rev G ph2 | Gi1 ph2 |
|--------|-----------|---------|-----------|---------|
| ADD | REG_WE→R1 | none | REG_WE→R2 | REG_WE→R0 |
| CMP | REG_WE→R1 | none | FLG_WE | FLG_WE |
| TFR | comb | **invalid** | — | — |

G-IC: 6 wires → **1** (`reg_we`). ALU B: `q_b`←R1 → **MBR→net_b**.

---

## Governance

- reference prose: no `cyclesim`/`pytest` command lines in edited files
- stale terms: no `inc_en`, `b_const_sel`, 14 DIP ALU BOM
