# dp_4reg_rsel — WinCUPL spike (P0)

**Parent:** [../../README.md](../../README.md)  
**Fork of:** `fit-study/variants/g_dual_dp/system_ctrl.pld` in [archive/fit-study-gpr-fsm.tar.gz](../../../../archive/fit-study-gpr-fsm.tar.gz)

---

## Purpose

Desk spike for **P0 naive 4-GPR**:

- R0–R3 (32 FF)
- `r_sel_a[1:0]`, `r_sel_b[1:0]` on G-IC
- 4:1 async muxes on `q_a`, `q_b`
- 4:1 xfer mux (ex-TFR `src`)

**Not for production burn** — pin declarations exceed ATF1504 32 user I/O.

---

## Files

| File | Role |
|------|------|
| [system_ctrl.pld](system_ctrl.pld) | CUPL equations + PIN declarations |
| [fit-desk.md](fit-desk.md) | Pin/MC desk result (no local WinCUPL run) |

---

## How to run (local)

```text
wincupl system_ctrl.pld system_ctrl.tt system_ctrl.jed
```

Expect fitter errors:

1. **Pin overflow** — 4 declared inputs beyond 32-user-I/O budget.
2. If pins forced: verify **Design fits** / MC count.

---

## Equation notes

- `rsa0/1`, `rsb0/1` = `r_sel_a`, `r_sel_b`.
- `q_a*` / `q_b*`: 4:1 mux over `r0*..r3*`.
- `xfer_b*`: 4:1 mux for write-from-register.
- `we_r3`: `reg_we & w_sel1 & w_sel0`.

---

## Related paths

| Path | This PLD |
|------|----------|
| P0 | Direct model |
| P2 STR-only | Do **not** use this PLD — use rev G + store mux on `q_a` only |
| P3 | External 574 — separate variant |
