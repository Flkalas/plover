# M3a — FSM control verification (no Flash CW burn)

| Field | Value |
|-------|-------|
| **Milestone** | M3a |
| **Goal** | Normative **FSM-only** opcode table verified; Flash `$4000` **unused** on v1.0 breadboard |
| **Normative** | [microcode-spec.md](../hardware/microcode-spec.md) · [cpld-system-controller.md](../hardware/cpld-system-controller.md) |

---

## 1. Concept

v1.0 does **not** program per-phase control words at Flash `$4000`. All sequenced macros (ADD, LDA, …) run from the **CPLD idx5 phase FSM**.

| Content | Location |
|---------|----------|
| ADD/LDA/STA/CMP templates | **CPLD FSM** (`opcode[4:0]` + phase) |
| Boot + program | SST39 ROM `$0000+` only |
| Flash `$4000–$4FFF` | **Reserved / unburned** |

---

## 2. Frozen FSM table (2026-07-07 Gi1)

**Result:** PASS — **16** FSM opcodes in idx5 LUT, **22** active idx5 slots (unique). **No TFR** comb in Gi1.

| Opcode | Template | Phase | idx5 | Gi1 strobes (summary) |
|--------|----------|-------|------|------------------------|
| 0x01 | ALU_REG | 0 | 4 | idle |
| 0x01 | ALU_REG | 1 | 5 | idle (no REG_WE) |
| 0x01 | ALU_REG | 2 | 6 | REG_WE→R0, FLG_WE, ADD |
| 0x02 | MEM_LD | 0 | 8 | MEM_RD |
| 0x02 | MEM_LD | 1 | 9 | REG_WE→R0 |
| 0x03 | MEM_ST | 0 | 12 | Y_OE |
| 0x03 | MEM_ST | 1 | 13 | MEM_WR |
| 0x04 | BEQ | 0 | 16 | ALU SUB |
| 0x04 | BEQ | 1 | 17 | PC_LOAD_EN≤Z |
| 0x05 | JMP | 0 | 20 | PC_LOAD_EN |
| 0x06 | CALL | 0 | 24 | PC_LOAD_EN |
| 0x07 | RET | 0 | 28 | PC_LOAD_EN |
| 0x08 | MEM_LD | 0 | 32 | MEM_RD |
| 0x08 | MEM_LD | 1 | 33 | REG_WE→R0 |
| 0x09 | MEM_ST | 0 | 36 | Y_OE |
| 0x09 | MEM_ST | 1 | 37 | MEM_WR |
| 0x0A | HALT | 0 | 40 | — |
| 0x0D | ALU_REG | 0 | 52 | idle |
| 0x0D | ALU_REG | 1 | 53 | idle |
| 0x0D | ALU_REG | 2 | 54 | FLG_WE, CMP |
| 0x0F | MEM_ST | 0 | 60 | Y_OE |
| 0x0F | MEM_ST | 1 | 61 | MEM_WR |

Opcode summary: `0x01` ADD · `0x02` LDA · `0x03` STA · `0x04` BEQ · `0x05` JMP · `0x06` CALL · `0x07` RET · `0x08` LDIO · `0x09` STIO · `0x0A` HALT · `0x0D` CMP · `0x0F` STA16. **`0x10–0x1F` invalid.**

Prior rev G table: [archive/rev-g-normative-snapshot/reference/hw-bringup/M3a-control-store.md](../../archive/rev-g-normative-snapshot/reference/hw-bringup/M3a-control-store.md).

Flash `$4000`: **unused** (FSM-only).

---

## 3. M3a sign-off

- [ ] Frozen table §2 matches Gi1 CU idx5 LUT (**22 rows** incl. CALL/RET)
- [ ] Gi1 **`system_ctrl_cu.jed`** and **`system_ctrl_dp.jed`** burned per [M2a-cpld-decode.md](M2a-cpld-decode.md)
- [ ] CALL/RET lab smoke — nested CALL/RET returns to caller ([M2a-cpld-decode.md](M2a-cpld-decode.md))
- [ ] CALL/RET CU fit — [research/call-ret-cu-fit/SUMMARY-REPORT.md](../../research/call-ret-cu-fit/SUMMARY-REPORT.md) gate
- [ ] No PARAM 574 on SoC bill of materials ([BOM.md](../project/BOM.md))
- [ ] Flash `$4000` region left empty for v1.0 bring-up

---

## Change log

| Date | Note |
|------|------|
| 2026-07-07 | CALL/RET — 16 opcodes, 22 idx5 rows |
| 2026-07-07 | Gi1 — idx5 row semantics; TFR removed |
| 2026-07-06 | rev G 20-row table archived |
