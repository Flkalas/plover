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

## 2. Software gate (before M3b wiring)

```bash
python tools/verify_control_store.py --v1.0
```

Expected: **PASS** — 16 FSM opcodes, idx5 slot coverage, TFR routing.

Optional empty stub (no param rows):

```bash
python tools/pack_control_store.py --hybrid --build-fixtures
```

---

## 3. Prototype Flash CW (archive only)

To exercise **10b CW** on a bench strap (`DECODE_BYPASS`), use the superseded prototype docs:

- [M3a legacy in prototype-flash-cw](../../archive/prototype-flash-cw/microcode-spec-v1.0.md)
- `python tools/verify_control_store.py --archive-flash-cw`
- `python tools/pack_control_store.py --build-fixtures` → `hw/fixtures/control/cw.hex`

---

## 4. M3a sign-off

- [ ] `verify_control_store.py --v1.0` PASS
- [ ] No PARAM 574 on SoC bill of materials ([BOM.md](../../BOM.md))
- [ ] Team agrees Flash `$4000` region left empty for v1.0 bring-up

---

## Change log

| Date | Note |
|------|------|
| 2026-06-24 | v1.0 FSM-only — hybrid Flash path moved to archive |
| 2026-06-10 | Prototype 10b CW (archive) |
