# Tier 2 migration (574 GPR → CPLD GPR + 138×2)

**Normative target:** [system-architecture.md](../../hardware/system-architecture.md) v0.2  
**Decisions:** [hardware-architecture-synthesis.md](../../hardware/hardware-architecture-synthesis.md) §10.1

---

## Overview

| Phase | Architecture | Docs |
|-------|--------------|------|
| **Tier 0 (legacy)** | 574×4 GPR + CPLD direct `/CE` | [cpld-system-controller-v0.1.md](../archive/pre-v0.1/cpld-system-controller-v0.1.md) |
| **Tier 2 (target)** | CPLD GPR + 138×2 + 574 FLG | [cpld-system-controller.md](../cpld-system-controller.md) v0.2 |

M1–M2b bring-up may complete on **Tier 0** before migration. **CPLD bitstream must be re-burned** for Tier 2 — not a patch on Tier 0 JED.

---

## Tier 0 legacy (optional stepping stone)

1. **M1** — ALU B3 ([M1-alu.md](M1-alu.md))
2. **M2a** — CPLD decode-only, direct CS ([M2a-cpld-decode.md](M2a-cpld-decode.md))
3. **M2b** — 574×4 GPR ↔ ALU ([M2b-gpr-memory.md](M2b-gpr-memory.md))

hwsim Tier 0: `regfile_574`, `mem_decode`, `cpld_gpr_decode`.

---

## Migration steps (after M2a verified)

### Step 1 — Wire 74HC138×2

- **138 #2** near SRAM/Flash: half-select (A15 / MAP).
- **138 #1:** CBA = A15,A14,A13; E gated by `!MAILBOX_EN` from CPLD.
- **08/32/04** glue → `RAM1_CS_N`, `RAM2_CS_N`, `ROM_CS_N`.
- Logic analyzer: Mode A/B spots @ `$0100`, `$0900`, `$8100`, `$FF00`, `$FFFC`.

Verify: `python -m hwsim run hw/tests/mem_decode_tier2.yaml`

### Step 2 — CPLD GPR synthesis

- Port list: [cpld-system-controller.md](../cpld-system-controller.md) v0.2.
- GPR reference: [cpld-hybrid-v1.3.md](../archive/pre-v0.1/cpld-hybrid-v1.3.md).
- If MC > 64 → **ATF1508** (1504 spare).

Verify: `python -m hwsim run hw/tests/cpld_regfile_dual_read.yaml`

### Step 3 — Retire 574 GPR

- Remove 574×4 GPR DIPs; keep **574×1 FLG** + PC/MBR/CW latches.
- Route `q_a`/`q_b` from ATF1504 to ALU (short stubs).

### Step 4 — Re-run M3+

- M3a CW / M3b fetch — use internal `w_sel` (no `LOAD_R*` wiring).
- M5 E2E on Tier 2 netlist.

---

## Do not buy

- **ATF16V8B GAL** — redundant with 138×2; no parasitic win ([synthesis §5.3](../../hardware/hardware-architecture-synthesis.md)).

---

## Simulator tiers

| Tier | hwsim tests |
|------|-------------|
| 0 | `regfile_574`, `mem_decode`, `cpld_gpr_decode` |
| 2 | `cpld_regfile_dual_read`, `mem_decode_tier2`, `cpld_gpr_decode_tier2` |

Both tiers run in `python -m hwsim run --all`.
