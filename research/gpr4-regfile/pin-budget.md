# Pin budget — 4-GPR on ATF1504AS-10JU44

**Device:** ATF1504AS-10JU44 PLCC-44 — **32 user I/O** (+ JTAG pins 7/13/32/38, `CLK` often pin 43)  
**Parent:** [proposal.md](proposal.md) · Baseline: [baseline-rev-g.md](baseline-rev-g.md)

Prior art: `fit-study/pin-budget-g-dual.md` in [archive/fit-study-gpr-fsm.tar.gz](../../archive/fit-study-gpr-fsm.tar.gz) (rev G **31/32 PASS**).

---

## 1. rev G CPLD-DP (reference)

| Direction | Signals | Count |
|-----------|---------|------:|
| **In** | `d_in[7:0]` | 8 |
| **In** | `reg_we`, `w_sel[1:0]`, `tfr_valid`, `src[1:0]` | 6 |
| **In** | `CLK` | 1 |
| **Out** | `q_a[7:0]`, `q_b[7:0]` | 16 |
| **Σ** | | **31** |

| vs 32 cap | **PASS** (1 spare) |

Declared pins in `g_dual_dp/system_ctrl.pld`: `d_in` on 1,2,4,5,6,8,9,11; G-IC on 12,14,16,17,18,19; `CLK` on 43.

---

## 2. P0 — naive 4-GPR + dual read select

### Assumptions

- Keep full **16** ALU outputs (`q_a`, `q_b`).
- Add **`r_sel_a[1:0]`**, **`r_sel_b[1:0]`** as DP inputs from CU.
- Keep **`d_in[7:0]`** on DP for LDA (all phases that latch from bus).
- Unified write: `reg_we`, `w_sel[1:0]`, `xfer` (ex-`tfr_valid`), `r_sel_src[1:0]` (ex-`src`) — **6** control wires (same count as rev G).

### Port table

| Direction | Signals | Count |
|-----------|---------|------:|
| **In** | `d_in[7:0]` | 8 |
| **In** | `reg_we`, `w_sel[1:0]`, `xfer`, `r_sel_src[1:0]` | 6 |
| **In** | **`r_sel_a[1:0]`, `r_sel_b[1:0]`** | **4** |
| **In** | `CLK` | 1 |
| **Out** | `q_a[7:0]`, `q_b[7:0]` | 16 |
| **Σ** | | **35** |

| vs 32 cap | **FAIL** — **+3 pins** |

### Arithmetic

```text
Δ inputs  = +4  (r_sel_a, r_sel_b)
Δ outputs =  0  (keep full q)
rev G     = 31
P0 total  = 35  →  overrun = 35 − 32 = 3
spare on rev G (1) does not cover deficit
```

**P0 verdict: FAIL on pin budget** (desk). MC may still fit (see [mc-estimate.md](mc-estimate.md)).

---

## 3. Cannot “borrow” spare from CPLD-CU

CPLD-CU has **6 spare** outputs (26/32 used), but every G-IC net needs a **DP input pad**. CU spare does not create DP input pins.

Routing more wires on the breadboard without DP pin declarations is not implementable inside the DP device.

---

## 4. Pin reduction options (desk)

| Tactic | Pins saved | Trade-off |
|--------|------------|-----------|
| Drop `q_b` to 4 bits | up to 4 | Breaks full 8b ALU B — **rejected** for v1.0 parity |
| Move `opc[4:0]` to DP | +5 in, −6 G-IC decode on CU | **Worse** (39+ I/O) |
| **Time-mux G-IC** (P1) | 2–4 | `sel[1:0]` reused by phase; CU FSM + timing proof |
| **STR-only** (P2) | 2–3 | Keep `q_a←R0`, `q_b←R1`; add `r_sel_st[1:0]` only for store |
| External GPR (P3) | DP outputs reduced | +574 BOM; fit-study A1 |
| ATF1508 (P4) | N/A | 64+ I/O device |

---

## 5. P1 — time-mux G-IC (sketch)

Reuse **`w_sel[1:0]`** and **`r_sel_src[1:0]`** as **`sel_a[1:0]`** / **`sel_b[1:0]`** depending on `gpr_phase[1:0]` from CU:

| `gpr_phase` | `sel_a` meaning | `sel_b` meaning |
|-------------|-----------------|-----------------|
| READ_ALU | `r_sel_a` | `r_sel_b` |
| WRITE | `w_sel` | don’t care |
| XFER | `r_sel_src` | `w_sel` (dst) |

**Wire count:** `reg_we` + `gpr_phase[1:0]` + `sel_a[1:0]` + `sel_b[1:0]` + `xfer` = **1+2+2+2+1 = 8** (+ `d_in`, `CLK`).

Compared to rev G G-IC (6): **+2 wires** → DP inputs **17** + 8 `d_in` + 1 `CLK` = **26 in**, 16 out = **42** — still **FAIL** unless `gpr_phase` is encoded in existing strobes or `d_in` is partially shared.

**LDA ph1 conflict:** ph1 needs all **8** `d_in` bits while ALU phases need **4** `r_sel` bits. If `r_sel` is only valid when `MEM_RD` is deasserted and bus is stable, **low nibble of `d_in` might time-share** during ph0/ph2 only — **needs timing table** vs [reference/hardware/alu-opcodes-timing.md](../../reference/hardware/alu-opcodes-timing.md). **P1: conditional, not proven.**

---

## 6. P2 — STR-only pin sketch

Keep rev G fixed ALU reads (`q_a=R0`, `q_b=R1`). Add only store-path select:

| Direction | Δ vs rev G |
|-----------|------------|
| In | +`r_sel_st[1:0]` (**2**) |
| Out | 0 |

**Total:** 31 + 2 = **33** → still **+1 FAIL** unless one G-IC wire is reclaimed (e.g. fold `tfr_valid`+`src` into STR/ADD microcode only).

If **TFR opcodes removed** and **STR** encodes src in opcode[1:0], CU can drive `r_sel_st` on **`src[1:0]`** during `Y_OE` phases only — **0 added wires**, **33 → 31 PASS** at cost of no generic `r_sel` on ALU.

---

## 7. CPLD-CU pin impact (4-GPR ISA)

CU does not hold GPR FF; impact is **LUT width** and optional **extra G-IC outputs**, not necessarily more CU pins if P2 encoding fits in existing 6 wires.

| Scenario | CU I/O |
|----------|--------|
| P0 (+4 G-IC) | 26 + 4 = **30**/32 — **PASS** on CU side |
| P2 (reuse `src` for STR) | **26**/32 unchanged |

CU is **not** the binding chip for P0; **DP is**.

---

## 8. Summary

| Path | DP total I/O | vs 32 | Verdict |
|------|-------------|------|---------|
| rev G (3-GPR) | 31 | −1 spare | **PASS** |
| **P0 naive** | **35** | **+3** | **FAIL** |
| P1 time-mux | 33–42 (variant-dependent) | TBD | **Investigate** |
| P2 STR-only (reuse wires) | **31** | 0 | **Conditional PASS** |
| P3 external GPR | ≤32 on DP | spare | **PASS** (BOM cost) |
| P4 ATF1508 | >>32 | — | **PASS** (different part) |

**Desk conclusion:** User proposal **verbatim on CPLD-DP ATF1504 fails pin budget by 3 pins.** See [feasibility-matrix.md](feasibility-matrix.md).
