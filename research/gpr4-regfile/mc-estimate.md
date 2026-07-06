# Macrocell desk estimate — 4-GPR CPLD-DP

**Device:** ATF1504AS-10JU44 — **64 macrocell** part rating (BOM label only; gate = WinCUPL **Design fits**)  
**Parent:** [pin-budget.md](pin-budget.md) · Baseline MC: [baseline-rev-g.md](baseline-rev-g.md)

**Label:** All figures below are **desk estimates** unless a local WinCUPL `.fit` log is attached under [variants/dp_4reg_rsel/fit-desk.md](variants/dp_4reg_rsel/fit-desk.md).

---

## 1. rev G CPLD-DP (baseline)

| Block | MC (desk) |
|-------|----------:|
| 3×8 GPR FF (r00–r27) | 24 |
| `we_r0..we_r2` decode | 3 |
| TFR 3:1 × 8 (`xfer_b*`) | 8–12 |
| `gpr_d` bus mux | 8 |
| `q_a`/`q_b` direct (no mux) | 0 |
| **Total** | **~18–28** |

Source: [reference/hardware/cpld-system-controller.md](../../reference/hardware/cpld-system-controller.md) §8.

Tier C monolithic reference (archived): **43 MC used** with trim `q` + CW bus — upper bound for “everything on one chip.”

---

## 2. Incremental cost — P0 4-GPR + selectable read

| Block | Δ MC | Notes |
|-------|-----:|-------|
| R3 (+8 FF) | **+8** | r30–r37 |
| `we_r3` | **+1** | `reg_we & w_sel1 & w_sel0` |
| TFR/xfer 3:1 → **4:1** × 8 | **+3–8** | one more minterm per bit |
| **`q_a` 4:1 mux × 8** | **+8–12** | was direct connect |
| **`q_b` 4:1 mux × 8** | **+8–12** | was direct connect |
| `r_sel_a/b` input buffers | **+2–4** | if routed to MC inputs |
| **Δ subtotal** | **~30–45** | |

### Combined estimate

```text
rev G DP     18–28 MC
P0 delta     30–45 MC (overlap possible; not double-counting FF)
P0 total     ~46–56 MC (desk range)
```

| vs 64 MC rating | **LIKELY PASS** |

Fitter may pack mux trees into shared product terms; pessimistic case approaches **56–60 MC** — still below 64 if pins were available.

---

## 3. Per-bit mux accounting (detail)

One bit of 4:1 mux (async to ALU):

```text
q_ax = !s1 & !s0 & r0x # !s1 & s0 & r1x # s1 & !s0 & r2x # s1 & s0 & r3x
```

Desk: **~1–1.5 MC per bit** for registered vs combinatorial output depending on fitter packing.  
×8 bits ×2 ports ≈ **16–24 MC** for read muxes alone (upper bound if not shared).

TFR 4:1 `xfer_b*`: same structure as one read mux → **+4–8 MC** over 3:1.

---

## 4. CPLD-CU MC (4-GPR ISA)

CU has **no GPR FF** in rev G. ISA expansion affects **idx5 LUT** and TFR decode:

| Change | Δ MC (desk) |
|--------|------------:|
| Remove 6-opc TFR OR | **−2–4** |
| Per-template `r_sel_a/b` in LUT | **+4–10** |
| STR opcode rows | **+2–4** |
| **Net CU** | **~29–40** (still likely ≤56) |

CU MC is **secondary** to DP for this study; pin budget fails before MC on P0.

---

## 5. Comparison to archived variants

| Variant | GPR | Read mux | MC note |
|---------|-----|----------|---------|
| rev G DP | 3×8 int | Fixed | ~18–28 |
| A1 external | off-chip | 574 | ~25 MC freed on CPLD |
| TFR-tmp-2op (E1) | 3+TMP | hidden 4th | +8 FF, 4-way `w_sel` |
| **P0 4-GPR** | 4×8 int | 2× 4:1 | ~46–56 desk |

---

## 6. Gate policy

Per project MC policy: **ATF1504 64 MC** is BOM rating only. Bring-up gate:

> WinCUPL **Design fits** on the forked PLD — not desk counts in normative docs.

For this research folder, record desk ranges and attach fitter output when available.

---

## 7. Summary

| Resource | P0 4-GPR on DP | Binding? |
|----------|----------------|----------|
| **Pins** | 35/32 **FAIL** | **Yes** |
| **MC** | ~46–56 / 64 **LIKELY PASS** | No (at desk) |

**MC is not the blocker; pins are.**
