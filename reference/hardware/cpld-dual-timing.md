# Dual CPLD timing (rev G)

**Clock:** 2.0 MHz · **Half-cycle:** 250 ns  
**Related:** [alu-opcodes-timing.md](alu-opcodes-timing.md)

---

## Critical paths (desk, frozen)

| Path | Total (ns) | Slack @ 250 ns |
|------|----------:|---------------:|
| **TFR latch** (CU→DP G-IC) | **40** | 210 |
| **Branch BEQ** (internal CU) | **212** | **38** |
| **P8 operand** (DP `q`→ALU) | **168** | 82 |

---

## TFR latch

`t_PD(CU) + t_wire + t_SETUP(DP)` = 15 + 10 + 15 = **40 ns**

---

## Branch BEQ

`t_ALU(SUB) + t_FLG + t_CU_merge + t_SETUP(PC) + wire` = 136 + 23 + 15 + 28 + 10 = **212 ns**

---

## System Fmax

**2.53 MHz** — limited by P8 operand path (unchanged from single-CPLD GPR read + ALU INC).

---

## Change log

| Date | Note |
|------|------|
| 2026-07-06 | rev G desk numbers promoted from fit-study |
