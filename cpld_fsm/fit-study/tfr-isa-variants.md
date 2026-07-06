# TFR ISA variants — fit-study

**Scope:** Research only — v1.0 [`microcode-spec.md`](../../reference/hardware/microcode-spec.md) §2.2 **unchanged**.

## Baseline (TFR-v10)

| Property | Value |
|----------|-------|
| Encoding | `opc[3:2]=dst`, `opc[1:0]=src` |
| Opcodes | `0x11`,`0x12`,`0x14`,`0x16`,`0x18`,`0x19` |
| Cycles | 1 phase |
| CPLD | 6-opc OR + 3-way src mux + `w_sel` from bits |

## TFR-3bit

| Property | Value |
|----------|-------|
| Encoding | `0x10 \| idx[2:0]` |
| Coverage | 6/6 pairs, 1 phase |
| CPLD | `tfr_valid = opc4 & !opc3` + idx LUT |
| SW | Compiler idx remap |

| idx | Transfer |
|-----|----------|
| 0 | R0←R1 |
| 1 | R0←R2 |
| 2 | R1←R0 |
| 3 | R1←R2 |
| 4 | R2←R0 |
| 5 | R2←R1 |

## TFR-ring-2bit

| `opc[1:0]` | Transfer |
|------------|----------|
| 00 | R0←R1 |
| 01 | R1←R2 |
| 10 | R2←R0 |
| 11 | reserved |

**Cold 3** (R0←R2, R1←R0, R2←R1): software **2-insn** ring sequence — **GPR clobber** on middle register.

PLD snippet: [`variants/e1_gpr_eeprom/tfr_ring.pld`](variants/e1_gpr_eeprom/tfr_ring.pld)

## TFR-ring-macro

Single opcode, **2-hop** through GPR ring — still **clobbers** middle GPR. Hardware phase FSM cost vs 2 SW insns.

## TFR-tmp-2op (4 registers)

| Reg | Role |
|-----|------|
| R0–R2 | Architectural (visible) |
| TMP | Hidden scratch |

**Every** transfer = 2 micro-ops: `TMP←src`; `dst←TMP`. **No GPR clobber.**

| `opc[1:0]` | Transfer |
|------------|----------|
| 00 | R0←R1 |
| 01 | R1←R2 |
| 10 | R2←R0 |
| 11 + `opc[3:2]` | cold 00=R0←R2, 01=R1←R0, 10=R2←R1 |

| HW axis | Options |
|---------|---------|
| TMP | CPLD +8 FF or external 574 |
| `w_sel` | 4-way |
| Phase | 2 per TFR insn |
| Pins | TMP not exported |

PLD snippet: [`variants/e1_gpr_eeprom/tfr_tmp_2op.pld`](variants/e1_gpr_eeprom/tfr_tmp_2op.pld)

## MC desk-check summary

| Variant | `tfr_valid` | Mux / FF | Phase | Net vs v1.0 |
|---------|-------------|----------|-------|-------------|
| v10 | 6-term OR | 3-way ×8 | 1 | baseline |
| 3bit | 1 term | idx LUT | 1 | **−OR** |
| ring-2bit | 3-term OR | fixed | 1 | **−OR** (3/6 only) |
| ring-macro | 3-term + FSM | ring ×2 | 2 | +FSM |
| tmp-2op | 2-bit + sub | 4-way + **+8 FF** | 2 | +FF, −OR |

Detail: [fit-logs/e1-tfr-isa-mc.md](fit-logs/e1-tfr-isa-mc.md)

## Simulation

| Module | Role |
|--------|------|
| [`sim/tfr_isa_models.py`](sim/tfr_isa_models.py) | Decoders + TMP micro-ops |
| [`tests/test_tfr_isa_variants.py`](tests/test_tfr_isa_variants.py) | Variant coverage |
