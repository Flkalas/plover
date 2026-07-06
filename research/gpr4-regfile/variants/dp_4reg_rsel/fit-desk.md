# Desk fit memo — dp_4reg_rsel (P0)

**Date:** 2026-07-07  
**Toolchain:** WinCUPL **not run** in CI / this session — desk analysis only  
**PLD:** [system_ctrl.pld](system_ctrl.pld)

---

## Pin declaration audit

### rev G baseline (g_dual_dp)

| Class | Count |
|-------|------:|
| Inputs (explicit PIN) | 15 (`d_in`×8 + G-IC×6 + `CLK`) |
| Outputs (`q_a`, `q_b`) | 16 |
| **Logical I/O** | **31** |

### P0 fork (this PLD)

| Class | Count |
|-------|------:|
| Inputs (explicit PIN) | **19** (+`r_sel_a`×2, +`r_sel_b`×2 on pins 20–23) |
| Outputs | 16 |
| **Logical I/O** | **35** |

| vs ATF1504AS 32 user I/O | **FAIL — overrun +3** |

### Explicit PIN list (research fork)

| Pin | Signal |
|-----|--------|
| 1,2,4,5,6,8,9,11 | `d_in[7:0]` |
| 12 | `reg_we` |
| 14,16 | `w_sel[1:0]` |
| 17 | `tfr_valid` |
| 18,19 | `src[1:0]` |
| **20,21** | **`r_sel_a[1:0]`** |
| **22,23** | **`r_sel_b[1:0]`** |
| 43 | `clk` |
| (fitter-assigned) | `q_a[7:0]`, `q_b[7:0]` |

JTAG reserved per device: 7, 13, 32, 38 — not used for logic.

**Desk verdict:** Fitter should report **insufficient pins** or require **PIN reassign** that still exceeds 32 bonded user I/O.

---

## Macrocell desk estimate

| Block | MC est. |
|-------|--------:|
| rev G DP core | 18–28 |
| +R3 FF | +8 |
| +`we_r3` | +1 |
| +`q_a` 4:1 ×8 | +8–12 |
| +`q_b` 4:1 ×8 | +8–12 |
| +xfer 4:1 ×8 | +3–8 |
| **Total** | **~46–56** |

| vs 64 MC rating | **LIKELY PASS** (if pins were available) |

---

## Expected WinCUPL outcome

| Check | Expected |
|-------|----------|
| Pin fit | **FAIL** |
| Design fits | **No** (pins first) |
| MC | Not reached / secondary |

---

## Next experiments

1. **P2 PLD:** rev G + internal mux `q_a` only during `tfr_valid` path for STR — 0 extra pins.
2. **P1:** Rewrite PIN block to time-mux `sel` onto `w_sel`/`src` — re-run fitter.
3. Attach real `.fit` log here when WinCUPL available locally.

---

## Changelog

| Date | Note |
|------|------|
| 2026-07-07 | Initial desk memo; no fitter invocation |
