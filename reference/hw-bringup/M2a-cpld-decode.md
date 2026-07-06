# M2a — Dual CPLD (rev G) bring-up

| Field | Value |
|-------|-------|
| **Milestone** | M2a |
| **IC** | 2× ATF1504AS-10JU44 (CPLD-CU + CPLD-DP) |
| **Goal** | WinCUPL JED burn (both chips); verify idx5 FSM, full `q`, ADD/TFR smoke |
| **Normative** | [cpld-system-controller.md](../hardware/cpld-system-controller.md) · [cpld-dual-jtag.md](../hardware/cpld-dual-jtag.md) · [M3a-control-store.md](M3a-control-store.md) §2 |

---

## 1. Why M2a after M1

| Order | Reason |
|-------|--------|
| After ALU (M1) | ALU path verified before CPLD-DP `q_a`/`q_b` |
| Before M2b/M3 | Both JEDs must drive ADD/TFR before fetch glue |
| CE decode | **138×2 + glue** — off CPLD |
| SoC decode | **No `alu8_decode` DIP** — strobes from **CPLD-CU** direct |

---

## 2. Repository artifacts

| Artifact | Role |
|----------|------|
| `system_ctrl_cu.pld` | CPLD-CU — idx5 FSM, strobes, G-IC |
| `system_ctrl_dp.pld` | CPLD-DP — GPR, full `q`, TFR mux |
| `ctrl_lut.inc` | Generated idx5 LUT (CU) |
| `system_ctrl_cu.jed` / `system_ctrl_dp.jed` | JTAG fuse files |

Codegen: `cpld_fsm/hdl/gen_ctrl_lut.py` · Build: `cpld_fsm/hdl/build-wincupl.ps1`

---

## 3. Pre-burn checklist

- [ ] **idx5 on CU:** `OPC[4:0]` from IR574
- [ ] **G-IC wired:** 6 signals CU→DP per [cpld-dual-routing.md](../hardware/cpld-dual-routing.md)
- [ ] **JTAG daisy chain:** CU first, then DP ([cpld-dual-jtag.md](../hardware/cpld-dual-jtag.md))
- [ ] **No CW latch** — Tier C archived
- [ ] **3 GPR on DP:** R0→`q_a`, R1→`q_b`, R2 internal
- [ ] **Fitter:** Design fits on **both** ATF1504AS
- [ ] **Frozen table:** 20 idx5 slots match M3a §2

---

## 4. Burn procedure

1. Program **`system_ctrl_cu.jed`** then **`system_ctrl_dp.jed`** via JTAG chain (or each chip standalone).
2. Read back device ID — ATF1504 family.
3. Power-cycle; verify CLK on both pin 43.

---

## 5. Bench vectors

Same idx5 keys as prior M2a — observe strobes on **CU**, `q_a`/`q_b` on **DP**.

### TFR20 (`0x18`)

REG_WE via G-IC; `w_sel=R2`; `src=R0`; DP latches R2←R0.

---

## 6. M2a sign-off

- [ ] Both JEDs readback OK
- [ ] ADD 3-phase strobes on CU (scope)
- [ ] TFR20 smoke on DP GPR
- [ ] G-IC bundle ≤ 10 cm

---

## Change log

| Date | Note |
|------|------|
| 2026-07-06 | **rev G** — dual CPLD; CW latch removed |
| 2026-07-06 | idx5, WinCUPL JED |
