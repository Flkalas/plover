# Microcode Specification v1.0 P12

**Normative:** v1.0 breadboard intent — **P12** pipe CU (PE1 machine + P12 discipline)  
**Related:** [cpld-pipe-cu.md](cpld-pipe-cu.md) · [rom-architecture.md](rom-architecture.md) · [cpld-system-controller.md](cpld-system-controller.md)

---

## 1. Architecture

| Axis | Choice | Rationale |
|------|--------|-----------|
| Opcode | Core `0x01–0x0F`; **`0x10–0x1F` reserved** | 5-bit opcode field `[4:0]` |
| Control | **Pipe CU** | IF\|EX / stall / stretch — [cpld-pipe-cu.md](cpld-pipe-cu.md) |
| Decode | **Pipe FSM** | Decode and strobes in CPLD-CU |
| CPLD | Dual ATF1504 | **CU:** pipe · **DP:** **R0 (AC) only**; **ALU B from MBR 574** |
| Control store | **CPLD FSM** | Strobes from pipe CU outputs |

Control lives in the CPLD pipe CU ([rom-architecture.md](rom-architecture.md) Flash map).

### 1.1 Pipe schedule

Active schedule = pipe states and SYS tax in [cpld-pipe-cu.md](cpld-pipe-cu.md). Every counted SYS does IF work, EX work, a documented stall/bubble, or stretch.

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

**Opcode group `0x10–0x1F`:** **reserved / trap**.

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

**P12:** lab fail → stretch (+1 visible). ADD/CMP use packed EX.

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

---

## 3. Control (pipe CU)

| Mechanism | Source |
|-----------|--------|
| GPR write | G-IC **`reg_we`** only — DP hardwires **R0** |
| `PC_LOAD_EN` | Opcode + `FLG_Z` on redirect EX |
| Operand imm8 | **MBR / oper latch** from IF |
| ALU / bus strobes | **CPLD-CU** pipe outputs |

Verify: [cpld-pipe-cu.md](cpld-pipe-cu.md).

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

G-IC is a single wire: `reg_we`.

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

CPLD drives `cin`, `bctrl0..3`, `lgc3:0`, `y_mux_sel` ([control-and-decode.md](control-and-decode.md)). M1 bench may use DIP decode separately.

**2 MHz desk:** EX ADD path ≈ **148 ns** in pipe budget ([cpld-pipe-cu.md](cpld-pipe-cu.md) §7); comb Y ≈ **133 ns** ([alu-opcodes-timing.md](alu-opcodes-timing.md)).

---

## 8. `/NMI`

Inactive (pull-up). No MMU/IRQ.
