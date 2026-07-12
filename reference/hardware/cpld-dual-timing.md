# Dual CPLD timing (Gi1)

**Clock:** 2.0 MHz 路 **Half-cycle:** 250 ns  
**Related:** [cpld-dual-timing.md](cpld-dual-timing.md) 路 [alu-opcodes-timing.md](alu-opcodes-timing.md) 路 [rom-comparison.md](rom-comparison.md) 路 [cu-dp-comparison.md](cu-dp-comparison.md) 路 [ttl-computer-comparison.md](ttl-computer-comparison.md) 路 [clock-comparison.md](clock-comparison.md) (peer clocks)

---

## Critical paths (desk, frozen)

| Path | Total (ns) | Slack @ 250 ns |
|------|----------:|---------------:|
| **Branch BEQ** (internal CU) | **212** | **38** |
| **P8 operand Gi1** (R0 `q_a` + MBR?払 parallel) | **~133** | **~117** |
| ~~TFR latch~~ | ??| **removed** (Gi1) |

---

## Gi1 ph2 ADD (execute)

Desk: R0?扐 (`q_a`) and MBR?払 in **parallel**; ALU Y ??**133 ns** ??dominant Gi1 execute path.

Prior rev G P8 @ 168 ns archived in [rev-g-dual-3gpr](../../archive/rev-g-dual-3gpr/README.md).

---

## Branch BEQ

`t_ALU(SUB) + t_FLG + t_CU_merge + t_SETUP(PC) + wire` = 136 + 23 + 15 + 28 + 10 = **212 ns**

---

## System Fmax (Gi1)

**> 3.7 MHz** on ph2 ADD desk path ??**2 MHz** normative clock retained for margin and multi-phase macros.

---

## Change log

| Date | Note |
|------|------|
| 2026-07-07 | Gi1 ??P8 ~133 ns; TFR path removed |
| 2026-07-06 | rev G desk numbers |
