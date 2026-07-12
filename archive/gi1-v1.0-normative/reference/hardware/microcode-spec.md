# Microcode Specification v1.0 (Gi1) (Gi1)

**Normative:** v1.0 breadboard — **Gi1** AC + MBR operand path (FSM-only idx5)  
**Related:** [rom-architecture.md](rom-architecture.md) · [cpld-system-controller.md](cpld-system-controller.md)  
**Superseded:** rev G 3-GPR + TFR — [archive/rev-g-dual-3gpr/README.md](../../archive/rev-g-dual-3gpr/README.md)

---

## 1. Architecture

| Axis | Choice | Rationale |
|------|--------|-----------|
| Opcode | **`op_legacy`** core; **`0x10–0x1F` reserved** (no TFR) | 5-bit opcode field `[4:0]` |
| Index | **`idx5`** | CPLD FSM key `(opcode[4:0]<<2)\|phase` — **128 logical slots** |
| Decode | **`dec_cpld_seq`** | Phase FSM in CPLD-CU; **no `alu8_decode`** |
| CPLD | **`cpld_dual_gi1`** | **CU:** idx5 + strobes · **DP:** **R0 (AC) only**; **ALU B from MBR 574** |
| CW/Flash | **`cw_fsm_only`** | **No Flash param/CW** — FSM opcode table only |

**No Flash fetch** at macro_start for control. Flash `$4000` region **unused** ([rom-architecture.md](rom-architecture.md)).

### 1.1 idx5 (CPLD internal only)

```text
fsm_index[6:0] = (opcode[4:0] << 2) | phase[1:0]
```

| | idx4 (archive) | idx5 (normative) |
|---|----------------|------------------|
| Opcode bits | `[3:0]` | **`[4:0]`** |
| Logical slots | 64 | **128** |
| Physical Flash | v1.0 `$4000` CW | **none** — CPLD PLA only |
| IR → CPLD | 4 wires | **5 wires** (`IR[4]` added) |

### 1.2 Operand datapath (Gi1)

| Port | Source |
|------|--------|
| ALU A | CPLD-DP `q_a` ← **R0** |
| ALU B | **MBR 574** `net_mbr[7:0]` → `net_b[7:0]` (off-chip wire) |
| GPR write | `d_in` → **R0** when `reg_we` (G-IC) |

**MBR hold:** During ALU_REG (ADD/CMP), operand byte latched at fetch must **not** reload until macro completes ([M3b-fetch-execute.md](../hw-bringup/M3b-fetch-execute.md)).

---

## 2. Macro ISA

### 2.0 Instruction formats (encoding)

Opcode field: **bits `[4:0]`** of the first instruction byte. Bits `[7:5]` are **reserved (0)** for normative opcodes.

| Format | Size | Layout |
|--------|------|--------|
| **Implied** | 1 B | `[7:5]=0`, `[4:0]=opcode` — HALT, **RET** |
| **Imm8** | 2 B | byte0: opcode; byte1: imm8 — LDA, STA, CMP, ADD, LDIO, STIO |
| **Abs16** | 3 B | byte0: opcode; bytes1–2: addr LE — BEQ, JMP, CALL, STA16 |

**Extended opcode group:** `0x10–0x1F` — **reserved / trap** (no TFR in v1.0 Gi1).

| Range | Use |
|-------|-----|
| `0x10–0x1F` | **Invalid** on breadboard (prior rev G TFR archived) |

### 2.1 Core (`0x01–0x0F`)

| Op | Mnemonic | Summary |
|----|----------|---------|
| `0x01` | ADD | **R0 ← R0 + imm** (3-phase) |
| `0x02` | LDA | Load from mem → R0 |
| `0x03` | STA | Store R0 to mem |
| `0x04` | BEQ | Branch if Z |
| `0x05` | JMP | Jump |
| `0x06` | CALL | Subroutine — push return PC; PC ← abs16 |
| `0x07` | RET | Return — pop return PC → PC |
| `0x08` | LDIO | Load MMIO → R0 |
| `0x09` | STIO | Store R0 to MMIO |
| `0x0A` | HALT | Stop |
| `0x0C` | — | **Reserved** (was MOV) |
| `0x0D` | CMP | R0 − imm (B from MBR); flags only |
| `0x0F` | STA16 | Store abs16 (boot) |

### 2.2 Phase counts (CPLD FSM)

| Op | Phases | Template |
|----|--------|----------|
| ADD | 3 | ALU_REG |
| LDA, LDIO | 2 | MEM_LD |
| STA, STIO, STA16 | 2 | MEM_ST |
| CMP | 3 | ALU_REG (flags_only) |
| BEQ | 2 | BEQ |
| JMP, HALT, CALL, RET | 1 | BRANCH / HALT |

### 2.3 Return stack (CU-assisted)

Gi1 has **no hardware RP register**. CALL/RET push/pop is performed by **CPLD-CU @ macro_end** using implicit `MEM_RD`/`MEM_WR` to RAM — not exposed as separate LDA/STA opcodes.

| Item | Normative value |
|------|-----------------|
| RP cell | `$0F00` / `$0F01` (16-bit LE) |
| Stack body | `$F600`–`$FEEF`, upward growth |
| Boot initial RP | `$F600` ([boot-jmp-handoff.md](../boot/boot-jmp-handoff.md)) |
| CALL @ macro_end | `return_pc` = address **after** 3-byte insn; `mem[RP]←return_pc` (16-bit LE); `RP+=2`; `PC←abs16` (from MBR) |
| RET @ macro_end | `RP-=2`; `PC←mem[RP]` (16-bit LE); **`PC_in` ≠ MBR** (popped word) |
| Overflow (`RP > $FEEF`) | execution **stops** (same as HALT — fetch ceases) |
| Underflow (`RP ≤ $F600`) | execution **stops** |
| Flash CW | **not used** — stack assist is CU sequencer logic |

Non-normative MC/pin fit study: [research/call-ret-cu-fit/SUMMARY-REPORT.md](../../research/call-ret-cu-fit/SUMMARY-REPORT.md). Peer TTL comparison: [ttl-computer-comparison.md](ttl-computer-comparison.md) §3.

---

## 3. FSM-only control (`cw_fsm_only`)

| Mechanism | Source |
|-----------|--------|
| GPR write | G-IC **`reg_we`** only — DP hardwires **R0** |
| `PC_LOAD_EN` | Opcode + `FLG_Z` @ macro_end |
| Operand imm8 | **MBR** from fetch (no internal R1 latch) |
| ALU / bus strobes | **CPLD-CU** direct outputs per §4 |

Verify: frozen FSM table in [M3a-control-store.md](../hw-bringup/M3a-control-store.md) §2 (**22 active idx5 slots**).

---

## 4. Per-phase control strobes

See [cpld-system-controller.md](cpld-system-controller.md) §7.

Summary:

| Template | Key strobes |
|----------|-------------|
| ALU_REG (ADD) | ph0–1: idle (no GPR write); ph2: `Y_OE`, `REG_WE`→R0, `FLG_WE`, ALU ADD |
| ALU_REG (CMP) | ph0–1: idle; ph2: `FLG_WE` only, ALU CMP; B from MBR |
| MEM_LD | ph0: MEM_RD; ph1: REG_WE → R0 |
| MEM_ST | ph0: Y_OE; ph1: MEM_WR |
| BEQ | ph0: ALU SUB; end: PC_LOAD_EN<=FLG_Z |
| JMP, CALL, RET | end: PC_LOAD_EN<=1 |

Bus and ALU strobes are **direct CPLD-CU outputs** (no CW latch). `REG_WE` reaches CPLD-DP via **G-IC** (`reg_we` only).

---

## 5. G-IC (CPLD-CU → DP)

| Signal | Function |
|--------|----------|
| `reg_we` | GPR write strobe — **always targets R0** in DP |

No `w_sel`, `tfr_valid`, or `src` on G-IC (Gi1).

---

## 6. Branch macros

| Op | `PC_LOAD_EN` @ macro_end | Operand / PC source |
|----|--------------------------|---------------------|
| BEQ | `FLG_Z` | abs16 in MBR |
| JMP | unconditional | abs16 in MBR |
| CALL | unconditional | abs16 in MBR; stack push @ macro_end |
| RET | unconditional | **popped return PC** (not MBR) |
| HALT | — | — |

CALL/RET stack assist: §2.3. Operand (abs16) for CALL latched in MBR during fetch — see [M3b-fetch-execute.md](../hw-bringup/M3b-fetch-execute.md).

---

## 7. ALU controls

CPLD drives `cin`, `bctrl0..3`, `lgc3:0`, `y_mux_sel` — no `alu8_decode` on SoC ([control-and-decode.md](control-and-decode.md)).

**2 MHz budget (Gi1 ph2 ADD):** Y ≈ **133 ns** @ 250 ns execute half ([alu-opcodes-timing.md](alu-opcodes-timing.md)).

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
| 2026-07-07 | **CALL/RET** — CU return-stack assist; 22 idx5 rows; RET implied |
| 2026-07-07 | **Gi1 v1.0** — AC + MBR→B; R0 only; TFR removed; G-IC 1-wire |
| 2026-07-06 | **rev G** archived — see [rev-g-dual-3gpr](../../archive/rev-g-dual-3gpr/README.md) |
| 2026-06-24 | idx5 FSM decode; ISA `[4:0]`; FSM-only |
| 2026-06-10 | v1.0 initial |
