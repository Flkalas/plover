# Microcode Specification v1.0 P12

**Normative:** v1.0 breadboard intent — **P12** pipe CU (PE1 machine + P12 discipline)  
**Related:** [cpld-pipe-cu.md](cpld-pipe-cu.md) · [rom-architecture.md](rom-architecture.md) · [cpld-system-controller.md](cpld-system-controller.md)  
**Superseded:** Gi1 idx5 multiphase — [archive/gi1-v1.0-normative/](../../archive/gi1-v1.0-normative/). Rev G 3-GPR + TFR — [archive/rev-g-dual-3gpr/](../../archive/rev-g-dual-3gpr/).

---

## 1. Architecture

| Axis | Choice | Rationale |
|------|--------|-----------|
| Opcode | **`op_legacy`** core; **`0x10–0x1F` reserved** (no TFR) | 5-bit opcode field `[4:0]` |
| Control | **Pipe CU** | IF\|EX / stall / stretch — [cpld-pipe-cu.md](cpld-pipe-cu.md) |
| Decode | **`dec_cpld_pipe`** | Pipe FSM in CPLD-CU; **no `alu8_decode`** |
| CPLD | **`cpld_dual_p12`** | **CU:** pipe · **DP:** **R0 (AC) only**; **ALU B from MBR 574** |
| CW/Flash | **`cw_fsm_only`** | **No Flash param/CW** |

**No Flash fetch** for control. Flash `$4000` region **unused** ([rom-architecture.md](rom-architecture.md)).

### 1.1 Pipe (not idx5 phase)

Gi1 `(opcode<<2)|phase` idle-capable tables are **archived**. Active schedule = pipe states and SYS tax in [cpld-pipe-cu.md](cpld-pipe-cu.md).

### 1.2 Operand datapath

| Port | Source |
|------|--------|
| ALU A | CPLD-DP `q_a` ← **R0** |
| ALU B | **MBR / operand latch** `net_mbr[7:0]` → `net_b[7:0]` |
| GPR write | `d_in` → **R0** when `reg_we` (G-IC) |

**MBR/oper hold:** During ADD/CMP EX, operand must **not** reload until the macro retires.

---

## 2. Macro ISA

### 2.0 Instruction formats (encoding)

Opcode field: **bits `[4:0]`** of the first instruction byte. Bits `[7:5]` are **reserved (0)** for normative opcodes.

| Format | Size | Layout |
|--------|------|--------|
| **Implied** | 1 B | `[7:5]=0`, `[4:0]=opcode` — HALT, **RET** |
| **Imm8** | 2 B | byte0: opcode; byte1: imm8 — LDA, STA, CMP, ADD, LDIO, STIO |
| **Abs16** | 3 B | byte0: opcode; bytes1–2: addr LE — BEQ, JMP, CALL, STA16 |

**Extended opcode group:** `0x10–0x1F` — **reserved / trap** (no TFR).

### 2.1 Core (`0x01–0x0F`)

| Op | Mnemonic | Summary |
|----|----------|---------|
| `0x01` | ADD | **R0 ← R0 + imm** |
| `0x02` | LDA | Load from mem → R0 |
| `0x03` | STA | Store R0 to mem |
| `0x04` | BEQ | Branch if Z |
| `0x05` | JMP | Jump |
| `0x06` | CALL | Subroutine — push return PC; PC ← abs16 |
| `0x07` | RET | Return — pop return PC → PC |
| `0x08` | LDIO | Load MMIO → R0 |
| `0x09` | STIO | Store R0 to MMIO |
| `0x0A` | HALT | Stop |
| `0x0C` | — | **Reserved** |
| `0x0D` | CMP | R0 − imm; flags only |
| `0x0F` | STA16 | Store abs16 (boot) |

### 2.2 Pipe SYS costs (optimistic)

Normative tax table: [cpld-pipe-cu.md](cpld-pipe-cu.md) §4. Summary:

| Op | Typical SYS (optimistic) |
|----|-------------------------:|
| ADD/CMP stream | **1** |
| ADD/CMP cold | **2** |
| LDA/STA/LDIO/STIO | **3** |
| BEQ taken / JMP | **4** |
| CALL | **6** |
| RET | **4** |
| HALT | **1** |

**P12:** lab fail → stretch (+1 visible). No Gi1 ADD/CMP idle phases.

### 2.3 Return stack (CU-assisted)

No hardware RP register. CALL/RET push/pop is performed by **CPLD-CU** in **STACK_EX** using implicit `MEM_RD`/`MEM_WR`.

| Item | Normative value |
|------|-----------------|
| RP cell | `$0F00` / `$0F01` (16-bit LE) |
| Stack body | `$F600`–`$FEEF`, upward growth |
| Boot initial RP | `$F600` ([boot-jmp-handoff.md](../boot/boot-jmp-handoff.md)) |
| CALL | `return_pc` after 3-byte insn; push; `PC←abs16` |
| RET | pop → `PC`; **`PC_in` ≠ MBR** |
| Overflow / underflow | execution **stops** |
| Flash CW | **not used** |

---

## 3. Control (`cw_fsm_only` + pipe)

| Mechanism | Source |
|-----------|--------|
| GPR write | G-IC **`reg_we`** only — DP hardwires **R0** |
| `PC_LOAD_EN` | Opcode + `FLG_Z` on redirect EX |
| Operand imm8 | **MBR / oper latch** from IF |
| ALU / bus strobes | **CPLD-CU** pipe outputs |

Verify: [cpld-pipe-cu.md](cpld-pipe-cu.md). Legacy Gi1 idx5 row lists are archived.

---

## 4. Per-op strobes (pipe EX)

See [cpld-pipe-cu.md](cpld-pipe-cu.md) §5.

| Class | Key EX strobes |
|-------|----------------|
| ADD | `Y_OE`, `REG_WE`→R0, `FLG_WE`, ALU ADD (single EX when packed) |
| CMP | `FLG_WE`, ALU CMP; B from MBR/oper |
| MEM_LD | `MEM_RD` + `REG_WE` (optimistic one EX) |
| MEM_ST | `Y_OE` + `MEM_WR` (optimistic one EX) |
| BEQ | flags path; `PC_LOAD_EN` if Z; bubble if taken |
| JMP / CALL / RET | `PC_LOAD_EN`; CALL/RET + stack EX |

Bus and ALU strobes are **direct CPLD-CU outputs**. `REG_WE` reaches CPLD-DP via **G-IC**.

---

## 5. G-IC (CPLD-CU → DP)

| Signal | Function |
|--------|----------|
| `reg_we` | GPR write strobe — **always targets R0** in DP |

No `w_sel`, `tfr_valid`, or `src` on G-IC.

---

## 6. Branch macros

| Op | `PC_LOAD_EN` | Operand / PC source |
|----|--------------|---------------------|
| BEQ | `FLG_Z` | abs16 latch |
| JMP | unconditional | abs16 latch |
| CALL | unconditional | abs16; stack push |
| RET | unconditional | **popped return PC** |
| HALT | — | — |

---

## 7. ALU controls

CPLD drives `cin`, `bctrl0..3`, `lgc3:0`, `y_mux_sel` — no `alu8_decode` on SoC ([control-and-decode.md](control-and-decode.md)).

**2 MHz desk:** EX ADD path ≈ **148 ns** in pipe budget ([cpld-pipe-cu.md](cpld-pipe-cu.md) §7); comb Y ≈ **133 ns** ([alu-opcodes-timing.md](alu-opcodes-timing.md)).

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
| 2026-07-13 | **v1.0 P12** — pipe SYS sheet; Gi1 idx5 idle schedule archived |
| 2026-07-07 | **CALL/RET** — CU return-stack assist |
| 2026-07-07 | **Gi1 v1.0** — AC + MBR→B; R0 only; TFR removed |
| 2026-07-06 | **rev G** archived |
| 2026-06-24 | idx5 FSM decode; ISA `[4:0]`; FSM-only |
| 2026-06-10 | v1.0 initial |
