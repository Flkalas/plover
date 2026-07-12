# M2a — Dual CPLD (Gi1) bring-up

| Field | Value |
|-------|-------|
| **Milestone** | M2a |
| **IC** | 2× ATF1504AS-10JU44 (CPLD-CU + CPLD-DP) |
| **Goal** | WinCUPL JED burn (both chips); verify idx5 FSM, R0/`q_a`, ADD smoke, **MBR→B** wire |
| **Normative** | [cpld-system-controller.md](../hardware/cpld-system-controller.md) · [cpld-dual-jtag.md](../hardware/cpld-dual-jtag.md) · [M3a-control-store.md](M3a-control-store.md) §2 |

---

## 1. Why M2a after M1

| Order | Reason |
|-------|--------|
| After ALU (M1) | ALU path verified before CPLD-DP `q_a` and MBR→B |
| Before M2b/M3 | Both JEDs must drive ADD before fetch glue |
| CE decode | **138×2 + glue** — off CPLD |
| SoC decode | **No `alu8_decode` DIP** — strobes from **CPLD-CU** direct |

---

## 2. Repository artifacts

| Artifact | Role |
|----------|------|
| Gi1 CU idx5 LUT | CPLD-CU — idx5 FSM, strobes, `reg_we` |
| Gi1 DP PLD fork | CPLD-DP — **R0 only**, `q_a` |
| `system_ctrl_cu.jed` / `system_ctrl_dp.jed` | JTAG fuse files |

**JTAG:** [cpld-dual-jtag.md](../hardware/cpld-dual-jtag.md). Prior rev G HDL: [archive/cpld-rev-g-hdl.tar.gz](../../archive/cpld-rev-g-hdl.tar.gz).

---

## 3. Pre-burn checklist

- [ ] **idx5 on CU:** `OPC[4:0]` from IR574
- [ ] **G-IC wired:** **`reg_we` only** CU→DP ([cpld-dual-routing.md](../hardware/cpld-dual-routing.md))
- [ ] **MBR→B:** `net_mbr0..7` → `net_b0..7` → ALU B
- [ ] **JTAG daisy chain:** CU first, then DP
- [ ] **R0 on DP:** `q_a` → ALU A; **no `q_b`**
- [ ] **Fitter:** Design fits on **both** ATF1504AS
- [ ] **Frozen table:** **22** idx5 slots match M3a §2 (Gi1 semantics incl. CALL/RET)
- [ ] **CALL/RET fit:** desk study in [p12-era-research](../../archive/p12-era-research/README.md) (`call-ret-cu-fit`) — restore tarball; gate before CU reburn if using that study

---

## 4. Burn procedure

1. Program **`system_ctrl_cu.jed`** then **`system_ctrl_dp.jed`** via JTAG chain.
2. Read back device ID — ATF1504 family.
3. Power-cycle; verify CLK on both pin 43.

---

## 5. Bench vectors

### ADD ph2 (`0x01`)

Preload R0; MBR holds imm8; ph2: `Y_OE`, `REG_WE`→R0, observe R0 ← R0+imm.

**Removed vs rev G:** TFR smoke — archived.

### CALL / RET smoke (post CU reburn)

1. ROM: `CALL` to subroutine; subroutine `RET`; verify PC returns to insn after CALL.
2. Nested `CALL` (depth ≥ 2) then matching `RET`s — stack cells at `$F600+` hold return PCs (16-bit LE).
3. Underflow: `RET` with RP=`$F600` → execution stops (HALT-class).

---

## 6. M2a sign-off

- [ ] Both JEDs readback OK
- [ ] ADD ph2 strobes on CU (scope)
- [ ] MBR→B wired; ALU B sees imm during ADD
- [ ] G-IC `reg_we` ≤ 10 cm
- [ ] CALL/RET smoke (§5) after CU JED with 22-row LUT

## Change log

| Date | Note |
|------|------|
| 2026-07-07 | CALL/RET — 22 idx5 slots; lab smoke |
| 2026-07-07 | Gi1 — R0 only; MBR→B; no TFR |
| 2026-07-06 | rev G archived |
