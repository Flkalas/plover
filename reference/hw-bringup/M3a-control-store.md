# M3a — FSM control verification (no Flash CW burn)

| Field | Value |
|-------|-------|
| **Milestone** | M3a |
| **Goal** | Normative **FSM-only** opcode table verified; Flash `$4000` **unused** on v1.0 breadboard |
| **Normative** | [microcode-spec.md](../hardware/microcode-spec.md) · [cpld-system-controller.md](../hardware/cpld-system-controller.md) |
| **Archive (prototype Flash CW)** | [prototype-flash-cw](../../archive/prototype-flash-cw/README.md) |

---

## 1. Concept

v1.0 does **not** program per-phase control words at Flash `$4000`. All sequenced macros (ADD, LDA, TFR, …) run from the **CPLD idx5 phase FSM**.

| Content | Location |
|---------|----------|
| ADD/LDA/STA/CMP/TFR templates | **CPLD FSM** (`opcode[4:0]` + phase) |
| Boot + program | SST39 ROM `$0000+` only |
| Flash `$4000–$4FFF` | **Reserved / unburned** |

---

## 2. Frozen FSM table (2026-07-06)

**Result:** PASS — 14 FSM opcodes in idx5 LUT, **20** active idx5 slots (unique). **TFR** uses comb `tfr_valid` (six opcodes § [microcode-spec.md](../hardware/microcode-spec.md) §2.2) — not idx5 rows.

| Opcode | Template | Phase | idx5 |
|--------|----------|-------|------|
| 0x01 | ALU_REG | 0 | 4 |
| 0x01 | ALU_REG | 1 | 5 |
| 0x01 | ALU_REG | 2 | 6 |
| 0x02 | MEM_LD | 0 | 8 |
| 0x02 | MEM_LD | 1 | 9 |
| 0x03 | MEM_ST | 0 | 12 |
| 0x03 | MEM_ST | 1 | 13 |
| 0x04 | BEQ | 0 | 16 |
| 0x04 | BEQ | 1 | 17 |
| 0x05 | JMP | 0 | 20 |
| 0x08 | MEM_LD | 0 | 32 |
| 0x08 | MEM_LD | 1 | 33 |
| 0x09 | MEM_ST | 0 | 36 |
| 0x09 | MEM_ST | 1 | 37 |
| 0x0A | HALT | 0 | 40 |
| 0x0D | ALU_REG | 0 | 52 |
| 0x0D | ALU_REG | 1 | 53 |
| 0x0D | ALU_REG | 2 | 54 |
| 0x0F | MEM_ST | 0 | 60 |
| 0x0F | MEM_ST | 1 | 61 |

Opcode summary: `0x01` ADD · `0x02` LDA · `0x03` STA · `0x04` BEQ · `0x05` JMP · `0x08` LDIO · `0x09` STIO · `0x0A` HALT · `0x0D` CMP · `0x0F` STA16 · TFR `0x11/12/14/16/18/19` (comb, not table).

Flash `$4000`: **unused** (FSM-only).

---

## 3. Prototype Flash CW (archive only)

Superseded **10b Flash CW** path — historical docs only:

- [prototype-flash-cw microcode-spec](../../archive/prototype-flash-cw/microcode-spec-v1.0.md)
- Archived tooling: [archived-code-guide.md](../../archive/MANIFEST.md)

---

## 4. M3a sign-off

- [ ] Frozen table §2 matches committed **`ctrl_lut.inc`** idx5 terms (same opcode/phase → same strobes)
- [ ] **`system_ctrl_cu.jed`** and **`system_ctrl_dp.jed`** burned per [M2a-cpld-decode.md](M2a-cpld-decode.md)
- [ ] No PARAM 574 on SoC bill of materials ([BOM.md](../project/BOM.md))
- [ ] Flash `$4000` region left empty for v1.0 bring-up

---

## Change log

| Date | Note |
|------|------|
| 2026-07-06 | 20-row idx5 table; TFR comb decode |
| 2026-07-06 | Sign-off: ctrl_lut.inc parity with §2; repository LUT artifact |
| 2026-07-04 | FSM table frozen in-doc; tool commands removed |
| 2026-06-24 | v1.0 FSM-only — hybrid Flash path moved to archive |
| 2026-06-10 | Prototype 10b CW (archive) |
