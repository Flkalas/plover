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

## 2. Frozen FSM table (2026-07-04)

**Result:** PASS — 16 FSM opcodes, **26** idx5 slots (unique), TFR routing verified before code archive.

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
| 0x10 | XFER | 0 | 64 |
| 0x11 | XFER | 0 | 68 |
| 0x12 | XFER | 0 | 72 |
| 0x13 | XFER | 0 | 76 |
| 0x14 | XFER | 0 | 80 |
| 0x15 | XFER | 0 | 84 |

Opcode summary: `0x01` ADD · `0x02` LDA · `0x03` STA · `0x04` BEQ · `0x05` JMP · `0x08` LDIO · `0x09` STIO · `0x0A` HALT · `0x0D` CMP · `0x0F` STA16 · `0x10–0x15` TFR.

Flash `$4000`: **unused** (FSM-only).

---

## 3. Prototype Flash CW (archive only)

Superseded **10b Flash CW** path — historical docs only:

- [prototype-flash-cw microcode-spec](../../archive/prototype-flash-cw/microcode-spec-v1.0.md)
- Archived tooling: [archived-code-guide.md](../../developer/archived-code-guide.md)

---

## 4. M3a sign-off

- [ ] Frozen table §2 matches CPLD JED (M2a)
- [ ] No PARAM 574 on SoC bill of materials ([BOM.md](../../BOM.md))
- [ ] Flash `$4000` region left empty for v1.0 bring-up

---

## Change log

| Date | Note |
|------|------|
| 2026-07-04 | FSM table frozen in-doc; tool commands removed |
| 2026-06-24 | v1.0 FSM-only — hybrid Flash path moved to archive |
| 2026-06-10 | Prototype 10b CW (archive) |
