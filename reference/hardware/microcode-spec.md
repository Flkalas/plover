# Microcode Specification v1.0

**Normative:** v1.0 breadboard (FSM-only idx5)  
**Related:** [rom-architecture.md](rom-architecture.md) · [cpld-system-controller.md](cpld-system-controller.md)  
**Superseded prototype:** [prototype-flash-cw](../archive/prototype-flash-cw/README.md)

---

## 1. Architecture

| Axis | Choice | Rationale |
|------|--------|-----------|
| Opcode | **`op_legacy`** core + **Extended `0x10–0x1F`** (TFR bit-field §2.2) | 5-bit opcode field `[4:0]` |
| Index | **`idx5`** | CPLD FSM key `(opcode[4:0]<<2)\|phase` — **128 logical slots** |
| Decode | **`dec_cpld_seq`** | Phase FSM in CPLD; **no `alu8_decode`** |
| CPLD | **`cpld_3fixed`** | R0→A, R1→B; R2 via internal read for XFER |
| CW/Flash | **`cw_fsm_only`** | **No Flash param/CW** — FSM opcode table only |

**No Flash fetch** at macro_start for control. Flash `$4000` region **unused** ([rom-architecture.md](rom-architecture.md)).

### 1.1 idx5 (CPLD internal only)

```text
fsm_index[6:0] = (opcode[4:0] << 2) | phase[1:0]
```

| | idx4 (archive / Pareto record) | idx5 (normative) |
|---|-------------------------------|------------------|
| Opcode bits | `[3:0]` | **`[4:0]`** |
| Logical slots | 64 | **128** |
| Physical Flash | v1.0 `$4000` CW | **none** — CPLD PLA only |
| IR → CPLD | 4 wires | **5 wires** (`IR[4]` added) |

---

## 2. Macro ISA

### 2.0 Instruction formats (encoding)

Opcode field: **bits `[4:0]`** of the first instruction byte. Bits `[7:5]` are **reserved (0)** for normative opcodes.

| Format | Size | Layout |
|--------|------|--------|
| **Implied** | 1 B | `[7:5]=0`, `[4:0]=opcode` — TFR, HALT |
| **Imm8** | 2 B | byte0: opcode; byte1: imm8 — LDA, STA, CMP, ADD, LDIO, STIO |
| **Abs16** | 3 B | byte0: opcode; bytes1–2: addr LE — BEQ, JMP, CALL, STA16 |

**Extended opcode group:** `0x10–0x1F` officially allocated.

| Range | Use |
|-------|-----|
| `0x11`, `0x12`, `0x14`, `0x16`, `0x18`, `0x19` | TFR (bit-field, normative) |
| `0x10`, `0x13`, `0x15`, `0x17`, `0x1A–0x1F` | Reserved / invalid TFR |

**TFR bit-field** (`opc[4]=1`): `opc[3:2]` = dst (00=R0, 01=R1, 10=R2), `opc[1:0]` = src; valid when src ≠ dst and neither field is `11₂`.

### 2.1 Core (`0x01–0x0F`)

| Op | Mnemonic | Summary |
|----|----------|---------|
| `0x01` | ADD | R2 ← R0 + R1 (3-phase) |
| `0x02` | LDA | Load from mem → R0 |
| `0x03` | STA | Store R0 to mem |
| `0x04` | BEQ | Branch if Z |
| `0x05` | JMP | Jump |
| `0x06` | CALL | Subroutine (TBD) |
| `0x07` | RET | Return (TBD) |
| `0x08` | LDIO | Load MMIO → R0 |
| `0x09` | STIO | Store R0 to MMIO |
| `0x0A` | HALT | Stop |
| `0x0C` | — | **Reserved** (was MOV) |
| `0x0D` | CMP | R0 − imm; flags only |
| `0x0F` | STA16 | Store abs16 (boot) |

### 2.2 Implied transfer (TFR bit-field)

| Op | Mnemonic | Action |
|----|----------|--------|
| `0x11` | TFR01 | R0 ← R1 |
| `0x12` | TFR02 | R0 ← R2 |
| `0x14` | TFR10 | R1 ← R0 |
| `0x16` | TFR12 | R1 ← R2 |
| `0x18` | TFR20 | R2 ← R0 |
| `0x19` | TFR21 | R2 ← R1 |

Encoding: `opcode = 0x10 \| (dst << 2) \| src` with dst/src ∈ {0,1,2}, src ≠ dst.

### 2.3 Phase counts (CPLD FSM)

| Op | Phases | Template |
|----|--------|----------|
| ADD | 3 | ALU_REG |
| LDA, LDIO | 2 | MEM_LD |
| STA, STIO, STA16 | 2 | MEM_ST |
| CMP | 3 | ALU_REG (flags_only) |
| TFR (6 opcodes §2.2) | 1 | XFER (comb decode, not idx5 LUT row) |
| BEQ | 2 | BEQ |
| JMP, HALT, CALL, RET | 1 | BRANCH |

---

## 3. FSM-only control (`cw_fsm_only`)

| Mechanism | Source |
|-----------|--------|
| `w_sel` | Internal FSM opcode/template table |
| `PC_LOAD_EN` | Opcode + `FLG_Z` @ macro_end |
| Operand address | **MBR** from fetch (no PARAM) |
| ALU / bus strobes | FSM registered outputs per §4 |

Verify: frozen FSM table in [M3a-control-store.md](../hw-bringup/M3a-control-store.md) §2 (2026-07-06, 20 rows).

---

## 4. Per-phase control strobes

See [cpld-system-controller.md](cpld-system-controller.md) §7 for full tables.

Summary:

| Template | Key strobes |
|----------|-------------|
| ALU_REG (ADD) | ph0–1: Y_OE; ph1: **REG_WE**, w_sel=R1 (mandatory); ph2: REG_WE, w_sel=R2, FLG_WE |
| ALU_REG (CMP) | ph0–1: same as ADD; ph2: **FLG_WE only** (flags_only — no REG_WE, no R2 latch) |
| MEM_LD | ph0: MEM_RD; ph1: REG_WE, w_sel=R0 |
| MEM_ST | ph0: Y_OE; ph1: MEM_WR |
| XFER | ph0: REG_WE, w_sel=dst; src via internal opcode mux |
| BEQ | ph0: ALU SUB; end: PC_LOAD_EN<=FLG_Z |
| JMP | end: PC_LOAD_EN<=1 |

**Tier C:** Bus and ALU strobes in the summary table are **held in CW_LO/CW_HI** 574 across each phase ([control-word-latch.md](control-word-latch.md)). `REG_WE` remains a direct CPLD output.

---

## 5. Internal `w_sel` (not exported)

| Template | Phase | `w_sel` |
|----------|-------|---------|
| ALU_REG (ADD) | ph2 | R2 |
| ALU_REG (ADD/CMP) | ph1 | R1 (**REG_WE mandatory** — imm8 operand latch) |
| MEM_LD | ph1 | R0 |
| XFER | ph0 | opcode bit-field → dst (`opc[3:2]`) |

### XFER opcode → (src, dst)

Bit-field: src = `opc[1:0]`, dst = `opc[3:2]`.

| Opcode | src | dst |
|--------|-----|-----|
| TFR01 `0x11` | R1 | R0 |
| TFR02 `0x12` | R2 | R0 |
| TFR10 `0x14` | R0 | R1 |
| TFR12 `0x16` | R2 | R1 |
| TFR20 `0x18` | R0 | R2 |
| TFR21 `0x19` | R1 | R2 |

---

## 6. Branch macros

| Op | `PC_LOAD_EN` @ macro_end |
|----|--------------------------|
| BEQ | `FLG_Z` |
| JMP | unconditional |
| CALL/RET/HALT | TBD |

Operand (abs16) latched in MBR during fetch — see [M3b-fetch-execute.md](../hw-bringup/M3b-fetch-execute.md).

---

## 7. ALU controls

CPLD drives `cin`, `bctrl0..3`, `lgc3:0`, `y_mux_sel` — no `alu8_decode` on SoC ([control-and-decode.md](control-and-decode.md)).

**2 MHz budget:** worst-case **INC 153 ns**, SUB **136 ns** ([alu-opcodes-timing.md](alu-opcodes-timing.md)).

---

## 8. `/NMI`

Inactive (pull-up). No MMU/IRQ.

---

## Appendix A — 16-bit CW (`cw16_direct`, P1 bench only)

P1 `DECODE_BYPASS` — not normative SoC path.

---

## Change log

| Date | Note |
|------|------|
| 2026-07-06 | Tier C CW latch footnote on per-phase strobes |
| 2026-07-06 | ALU_REG ADD vs CMP ph2 split; mandatory ph1 REG_WE for ADD/CMP |
| 2026-06-24 | idx5 FSM decode; ISA `[4:0]`; per-phase strobes; operand datapath |
| 2026-07-06 | TFR bit-field opcodes; idx5 20 rows; `tfr_valid` comb |
| 2026-06-24 | FSM-only; TFR bit-field; `0x0C` reserved |
| 2026-06-10 | v1.0 archived |
