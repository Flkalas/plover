# M3a — Pipe CU control verification (no Flash CW burn)

| Field | Value |
|-------|-------|
| **Milestone** | M3a |
| **Goal** | Verify Active **pipe CU** control ownership; Flash `$4000` **unused** |
| **Normative** | [cpld-pipe-cu.md](../hardware/cpld-pipe-cu.md) · [microcode-spec.md](../hardware/microcode-spec.md) · [cpld-system-controller.md](../hardware/cpld-system-controller.md) |

---

## 1. Concept

v1.0 does **not** program control words at Flash `$4000`. Active control is the **pipe CU** ([cpld-pipe-cu.md](../hardware/cpld-pipe-cu.md)).

| Content | Location |
|---------|----------|
| IF\|EX / stall / stretch / STACK_EX | **CPLD-CU** pipe FSM |
| Boot + program | SST39 ROM `$0000+` only |
| Flash `$4000–$4FFF` | **Reserved / unburned** |

---

## 2. Active verify sheet

Use the pipe SYS / state tables — **not** multiphase idle rows:

| Check | Source |
|-------|--------|
| States FILL / IF_EX / OPERAND_IF / MEM_STALL / BRANCH_BUBBLE / STACK_EX / STRETCH | [cpld-pipe-cu.md](../hardware/cpld-pipe-cu.md) §3 |
| Per-op SYS tax (ADD, LDA, BEQ, CALL, …) | [cpld-pipe-cu.md](../hardware/cpld-pipe-cu.md) §4 · [microcode-spec.md](../hardware/microcode-spec.md) |
| Opcode set `0x01–0x0F`; `0x10–0x1F` invalid | [microcode-spec.md](../hardware/microcode-spec.md) §2 |
| CALL/RET fit desk | [cpld-pipe-cu.md](../hardware/cpld-pipe-cu.md) §5.1 |

---

## 3. M3a sign-off

- [ ] Pipe CU **Design fits** (when `.pld` exists) or interim CU JED matches Active strobe intent
- [ ] **`system_ctrl_cu.jed`** and **`system_ctrl_dp.jed`** burned per [M2a-cpld-decode.md](M2a-cpld-decode.md)
- [ ] CALL/RET lab smoke — nested CALL/RET returns to caller ([M2a-cpld-decode.md](M2a-cpld-decode.md))
- [ ] CALL/RET CU fit — [cpld-pipe-cu.md](../hardware/cpld-pipe-cu.md) §5.1
- [ ] No PARAM 574 on SoC bill of materials ([BOM.md](../project/BOM.md))
- [ ] Flash `$4000` region left empty for v1.0 bring-up
- [ ] Multiphase idle / padding phases **not** used as Active verify

---

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Retarget verify to pipe CU; drop multiphase table as Active |
| 2026-07-07 | CALL/RET smoke gates |
