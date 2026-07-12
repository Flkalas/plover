# M5 — Integrated CPU E2E (breadboard regression)

| Field | Value |
|-------|-------|
| **Milestone** | M5 |
| **Goal** | Breadboard wiring captured as a **frozen checklist** |
| **Status** | Deferred — active repo is **document-only** |
| **선행** | M2b–M4b breadboard smoke |

---

## 1. Scope (v1.0)

M5 is **not** a new solder step. After M1–M4b pass on hardware:

1. Photograph / netlist log matches [breadboard-wiring.md](breadboard-wiring.md)
2. F6 trace from [M3b-fetch-execute.md](M3b-fetch-execute.md) matches pipe CU / ISA ([cpld-pipe-cu.md](../hardware/cpld-pipe-cu.md), [microcode-spec.md](../hardware/microcode-spec.md))

Sign-off against frozen fixtures in [fixtures](../fixtures/).

---

## 2. M5 sign-off

- [ ] Composite breadboard matches normative block diagram
- [ ] M3b F6 GPR snapshot documented (lab log)
- [ ] No Flash `$4000` CW programmed

---

## 3. Note

v1.0 SoC uses **CPLD FSM only** — no `$4000` CW addr mux in M5 target path.
