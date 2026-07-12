# M2a — Dual CPLD bring-up (v1.0)

| Field | Value |
|-------|-------|
| **Milestone** | M2a |
| **IC** | 2× ATF1504AS-10JU44 (CPLD-CU + CPLD-DP) |
| **Goal** | WinCUPL JED burn (both chips); verify CU strobes, R0/`q_a`, ADD smoke, **MBR→B** wire |
| **Normative** | [cpld-system-controller.md](../hardware/cpld-system-controller.md) · [cpld-pipe-cu.md](../hardware/cpld-pipe-cu.md) · [cpld-dual-jtag.md](../hardware/cpld-dual-jtag.md) |

---

## 1. Why M2a after M1

| Order | Reason |
|-------|--------|
| After ALU (M1) | ALU path verified before CPLD-DP `q_a` and MBR→B |
| Before M2b/M3 | Both JEDs must drive ADD before fetch glue |
| CE decode | **138×2 + glue** — off CPLD |
| SoC decode | Strobes from **CPLD-CU** direct |

---

## 2. Repository artifacts

| Artifact | Role |
|----------|------|
| CU PLD | CPLD-CU — pipe / strobes, `reg_we` (**Design fits pending**) |
| DP PLD | CPLD-DP — **R0 only**, `q_a` |
| `system_ctrl_cu.jed` / `system_ctrl_dp.jed` | JTAG fuse files |

**JTAG:** [cpld-dual-jtag.md](../hardware/cpld-dual-jtag.md).

---

## 3. Pre-burn checklist

- [ ] **OPC on CU:** `OPC[4:0]` from IR574
- [ ] **G-IC wired:** **`reg_we` only** CU→DP ([cpld-dual-routing.md](../hardware/cpld-dual-routing.md))
- [ ] **MBR→B:** `net_mbr0..7` → `net_b0..7` → ALU B
- [ ] **JTAG daisy chain:** CU first, then DP
- [ ] **R0 on DP:** `q_a` → ALU A
- [ ] **ALU B:** MBR → `net_b`
- [ ] **Fitter:** Design fits on **both** ATF1504AS
- [ ] **ISA table:** CALL/RET included; align with [microcode-spec.md](../hardware/microcode-spec.md)
- [ ] **CALL/RET fit:** [cpld-pipe-cu.md](../hardware/cpld-pipe-cu.md) §5.1 conditions before CU reburn

---

## 4. Burn procedure

1. Program **`system_ctrl_cu.jed`** then **`system_ctrl_dp.jed`** via JTAG chain.
2. Read back device ID — ATF1504 family.
3. Power-cycle; verify CLK on both pin 43.

---

## 5. Bench vectors

### ADD EX (`0x01`)

Preload R0; MBR holds imm8; EX: `Y_OE`, `REG_WE`→R0, observe R0 ← R0+imm.

Opcodes `0x10–0x1F` are reserved.

### CALL / RET smoke (post CU reburn)

1. ROM: `CALL` to subroutine; subroutine `RET`; verify PC returns to insn after CALL.
2. Nested `CALL` (depth ≥ 2) then matching `RET`s — stack cells at `$F600+` hold return PCs (16-bit LE).
3. Underflow: `RET` with RP=`$F600` → execution stops (HALT-class).

---

## 6. M2a sign-off

- [ ] Both JEDs readback OK
- [ ] ADD EX strobes on CU (scope)
- [ ] MBR→B wired; ALU B sees imm during ADD
- [ ] G-IC `reg_we` ≤ 10 cm
- [ ] CALL/RET smoke (§5) after CU JED
