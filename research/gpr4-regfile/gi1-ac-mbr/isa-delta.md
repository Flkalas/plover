# Gi1 ISA delta

**Parent:** [README.md](README.md)  
**Normative baseline:** [reference/hardware/microcode-spec.md](../../../reference/hardware/microcode-spec.md) — unchanged in this folder

---

## 1. Design goal

| Goal | Gi1 means |
|------|-----------|
| 250 ns ph2 @ 2 MHz | MBR→B + R0→A parallel |
| No TFR traffic | **AC writeback**; spills to **RAM** |
| Gigatron-like model | **One visible GPR (R0)** in CPLD |

---

## 2. Opcode semantics (desk proposal)

| Op | rev G | **Gi1** |
|----|-------|---------|
| `ADD #imm` | R2 ← R0 + imm | **R0 ← R0 + imm** |
| `CMP #imm` | flags; ph1 imm→R1 | **flags only**; B from **MBR** |
| `LDA #imm` | R0 ← mem | unchanged |
| `STA #imm` | mem ← R0 | unchanged |
| `LDIO` / `STIO` | R0 | unchanged |
| `BEQ` / `JMP` / `CALL` / `RET` | unchanged encoding | unchanged (MBR = address) |
| `TFR` `0x11–0x19` | 6 implied moves | **invalid / reserved** |
| `0x0C` | reserved | reserved |
| `HALT` | unchanged | unchanged |

**Mnemonic names unchanged** where opcode bytes stay — **meaning** of ADD/CMP changes.

---

## 3. Register model

| Register | rev G | Gi1 |
|----------|-------|-----|
| **R0** | AC; ALU A | **AC**; ALU A; **ALU result** |
| **R1** | imm latch; ALU B | **removed** from CPLD |
| **R2** | ADD result; TFR | **removed** from CPLD |
| **R3** | — | — |
| **MBR** | fetch operand / address | **ALU B** for ALU_REG |
| **PC, IR, FLG** | external 574 | unchanged |

**Programmer rule:** Additional variables live in **RAM** (like Gigatron heap / Isetta RAM registers).

---

## 4. Macro phases

### ADD (`0x01`)

| Phase | rev G | Gi1 (desk) |
|-------|-------|------------|
| ph0 | `Y_OE` (display path) | **optional NOP / bus** — must **not** reload MBR |
| ph1 | `REG_WE` → **R1** (mandatory) | **no GPR write** (or idle) |
| ph2 | ALU; `REG_WE` → **R2**; `FLG_WE` | ALU; `REG_WE` → **R0**; `FLG_WE` |

**2-phase variant (research option):** ph0+ph1 merged → faster macro wall-clock; ph2 still 250 ns.

### CMP (`0x0D`)

| Phase | Gi1 |
|-------|-----|
| ph2 | `FLG_WE` only — **no** `REG_WE` (same policy as rev G) |

### LDA / STA

Unchanged vs normative — MBR used as **address**, not ALU B during those macros.

---

## 5. Software migration

| rev G pattern | Gi1 replacement |
|---------------|-----------------|
| `ADD #x` … `TFR02` … `STA` | `ADD #x` … `STA` (result already in R0) |
| `ADD` leaving R0 intact | **not supported** — save R0 to mem first |
| `CMP` then `ADD` reusing R1 imm | **N/A** — imm always from **current** insn MBR |
| [m3b_mini.hex](../../../simulators/cyclesim/fixtures/m3b_mini.hex) | **incompatible** — Gi1 ROM needed |

---

## 6. vs 4-GPR proposal

[../proposal.md](../proposal.md) targeted selectable `r_sel` + STR. **Gi1 explicitly abandons** that for **timing + pin headroom**.

---

## 7. cyclesim (future, out of scope)

| Module | Change |
|--------|--------|
| `dp.py` | 1 reg; no `qb()` from R1 |
| `gic.py` | drop `tfr_valid`, `w_sel` |
| `isa.py` | ADD w_sel R0; drop TFR_OPS |

Document only — no sim changes in this research folder.

---

## Related

- [fsm-microcode-delta.md](fsm-microcode-delta.md)
- [architecture.md](architecture.md)
