# Microcode Specification v0.1

**Related:** [rom-architecture.md](rom-architecture.md) · [cpld-system-controller.md](cpld-system-controller.md)

---

## 1. Macro ISA (draft GPR machine)

| Op | Mnemonic | Summary |
|----|----------|---------|
| `0x01` | ADD | Rdst ← R0 op R1 (phased) |
| `0x02` | LDA | Load from mem |
| `0x03` | STA | Store to mem |
| `0x04` | BEQ | Branch if Z |
| `0x05` | JMP | Jump |
| `0x06` | CALL | Subroutine |
| `0x07` | RET | Return |
| `0x08` | LDIO | Load from `$FF00+` |
| `0x09` | STIO | Store to MMIO |
| `0x0A` | HALT | Stop |

Operand byte follows opcode (2-byte header) unless extended by micro-sequence.

---

## 2. Eight-bit control word

| Bit | Signal |
|-----|--------|
| B7–B4 | `ALU_OP[3:0]` |
| B3 | `REG_WE` |
| B2 | `Y_OE` |
| B1 | `MEM_RD` |
| B0 | `MEM_WR` |

Pack: `tools/pack_control_store.py` · Flash base **`$4000`**.

---

## 3. Micro-sequences and Reg_Sel (CPLD)

Each macro opcode runs **1–3 micro-phases**. Control-store index and Flash address:

```
store_index = ((opcode[3:0] << 2) | phase[1:0])
Flash_addr  = $4000 + store_index
```

`Reg_Sel[1:0]` is decoded by the CPLD from `{opcode[3:0], phase[1:0]}` — **not** encoded in the CW.

Packed rows below match `tools/pack_control_store.py` → `hw/fixtures/control/cw.hex`.
Verify: `python tools/verify_control_store.py`.

### Summary (packed in Flash)

| Op | Phases | Store idx (ph0…) | CW (ph0…) | Status |
|----|--------|------------------|-----------|--------|
| ADD `0x01` | 3 | 4, 5, 6 | `14`, `14`, `1C` | packed |
| LDA `0x02` | 2 | 8, 9 | `02`, `08` | packed |
| STA `0x03` | 2 | 12, 13 | `04`, `01` | packed |
| BEQ `0x04` | 2 | 16, 17 | `20`, `00` | packed |
| CMP `0x0D` | 3 | 52, 53, 54 | `B0`, `B0`, `00` | packed |
| JMP `0x05` | 1 | 20 | `00` | packed |
| CALL `0x06` | 1 | 24 | `00` | packed |
| RET `0x07` | 1 | 28 | `00` | packed |
| HALT `0x0A` | 1 | 40 | `00` | packed |
| LDIO `0x08` | — | — | — | TBD |
| STIO `0x09` | — | — | — | TBD |

CW `00` means all control bits deasserted (ALU NOP). Unprogrammed slots also read `00`; macro **phase count** (see `plover_vm/macro/isa.py`) terminates the sequence.

---

### ADD (`0x01`)

| Ph | Idx | Flash | CW | Reg_Sel | ALU | REG_WE | Y_OE | MEM_RD | MEM_WR | Action |
|----|-----|-------|-----|---------|-----|--------|------|--------|--------|--------|
| 0 | 4 | `$4004` | `14` | 00 (R0) | ADD | 0 | 1 | 0 | 0 | Drive ALU A ← R0 |
| 1 | 5 | `$4005` | `14` | 01 (R1) | ADD | 0 | 1 | 0 | 0 | Drive ALU B ← R1 |
| 2 | 6 | `$4006` | `1C` | 10 (R2) | ADD | 1 | 1 | 0 | 0 | Latch ALU Y → Rdst |

---

### LDA (`0x02`)

| Ph | Idx | Flash | CW | Reg_Sel | ALU | REG_WE | Y_OE | MEM_RD | MEM_WR | Action |
|----|-----|-------|-----|---------|-----|--------|------|--------|--------|--------|
| 0 | 8 | `$4008` | `02` | 00 | NOP | 0 | 0 | 1 | 0 | `[operand]` → bus |
| 1 | 9 | `$4009` | `08` | 00 | NOP | 1 | 0 | 0 | 0 | Bus → R0 |

---

### STA (`0x03`)

| Ph | Idx | Flash | CW | Reg_Sel | ALU | REG_WE | Y_OE | MEM_RD | MEM_WR | Action |
|----|-----|-------|-----|---------|-----|--------|------|--------|--------|--------|
| 0 | 12 | `$400C` | `04` | 00 | NOP | 0 | 1 | 0 | 0 | R0 → bus (via ALU Y) |
| 1 | 13 | `$400D` | `01` | 00 | NOP | 0 | 0 | 0 | 1 | Write bus to `[operand]` |

---

### BEQ (`0x04`)

Compare via ALU SUB; branch decision uses latched **Z** from phase 0 (macro engine).  
**Y_OE=0** on compare phase — flags only; ALU Y must not drive the data bus.

| Ph | Idx | Flash | CW | Reg_Sel | ALU | REG_WE | Y_OE | MEM_RD | MEM_WR | Action |
|----|-----|-------|-----|---------|-----|--------|------|--------|--------|--------|
| 0 | 16 | `$4010` | `20` | 00 | SUB | 0 | **0** | 0 | 0 | R0 − imm; update Z/C (no bus drive) |
| 1 | 17 | `$4011` | `00` | 00 | NOP | 0 | 0 | 0 | 0 | Macro: PC ← target if Z |

---

### CMP (`0x0D`)

R0 − imm; **flags only** (discard Y). Uses **`CW_CMP_EXEC`** = `0xB0` (`ALU_OP=CMP`, `Y_OE=0`, `REG_WE=0`).

| Ph | Idx | Flash | CW | Reg_Sel | ALU | REG_WE | Y_OE | MEM_RD | MEM_WR | Action |
|----|-----|-------|-----|---------|-----|--------|------|--------|--------|--------|
| 0 | 52 | `$4034` | `B0` | 00 (R0) | CMP | 0 | **0** | 0 | 0 | A ← R0 |
| 1 | 53 | `$4035` | `B0` | 01 (imm) | CMP | 0 | **0** | 0 | 0 | B ← imm; SUB flags settle |
| 2 | 54 | `$4036` | `00` | — | NOP | 0 | 0 | 0 | 0 | (optional FLG latch ph — CPLD) |

hwsim bus gate: [`cmp_y_oe_bus`](../hw/tests/cmp_y_oe_bus.yaml) — `Y_OE=1` drives `net_d*`; `Y_OE=0` → tri-state.

---

### JMP (`0x05`)

| Ph | Idx | Flash | CW | Reg_Sel | ALU | REG_WE | Y_OE | MEM_RD | MEM_WR | Action |
|----|-----|-------|-----|---------|-----|--------|------|--------|--------|--------|
| 0 | 20 | `$4014` | `00` | 00 | NOP | 0 | 0 | 0 | 0 | Macro: PC ← `[operand]` |

---

### HALT (`0x0A`)

| Ph | Idx | Flash | CW | Reg_Sel | ALU | REG_WE | Y_OE | MEM_RD | MEM_WR | Action |
|----|-----|-------|-----|---------|-----|--------|------|--------|--------|--------|
| 0 | 40 | `$4028` | `00` | 00 | NOP | 0 | 0 | 0 | 0 | Macro: stop fetch/decode |

---

### CALL (`0x06`) — planned, not packed

| Ph | Reg_Sel | REG_WE | MEM_RD | MEM_WR | Action (draft) |
|----|---------|--------|--------|--------|----------------|
| 0 | 00 | 0 | 0 | 0 | Push return PC; PC ← `[operand]` (macro + stack TBD) |

*No rows in `cw.hex` yet. Target phase count: 1 (stub) until stack micro-sequence is defined.*

---

### RET (`0x07`) — planned, not packed

| Ph | Reg_Sel | REG_WE | MEM_RD | MEM_WR | Action (draft) |
|----|---------|--------|--------|--------|----------------|
| 0 | 00 | 0 | 0 | 0 | PC ← popped return address (macro + stack TBD) |

*No rows in `cw.hex` yet.*

---

### LDIO (`0x08`) — packed

Same CW pattern as LDA; effective address `0xFF00 | (imm8 & 0xFF)` (CPLD `MAILBOX_EN`).

| Ph | Reg_Sel | ALU | REG_WE | Y_OE | MEM_RD | MEM_WR | Action (draft) |
|----|---------|-----|--------|------|--------|--------|----------------|
| 0 | 00 | NOP | 0 | 0 | 1 | 0 | MMIO read → bus |
| 1 | 00 | NOP | 1 | 0 | 0 | 0 | Bus → R0 |

Packed: ph0 `02`, ph1 `08` (same as LDA).

---

### STIO (`0x09`) — packed

Same CW pattern as STA; MMIO write via CPLD decode.

| Ph | Reg_Sel | ALU | REG_WE | Y_OE | MEM_RD | MEM_WR | Action (draft) |
|----|---------|-----|--------|------|--------|--------|----------------|
| 0 | 00 | NOP | 0 | 1 | 0 | 0 | R0 → bus |
| 1 | 00 | NOP | 0 | 0 | 0 | 1 | Write bus to MMIO `[operand]` |

Packed: ph0 `04`, ph1 `01` (same as STA).

---

### MOV (`0x0C`) — packed

| Ph | Idx | Flash | CW | Action |
|----|-----|-------|-----|--------|
| 0 | 48 | `$4030` | `00` | Macro: `R[dst] ← R[src]` (`imm = (dst<<4)|src`) |

---

### STA16 (`0x0F`) — packed (boot)

| Ph | Idx | Flash | CW | Reg_Sel | ALU | REG_WE | Y_OE | MEM_RD | MEM_WR | Action |
|----|-----|-------|-----|---------|-----|--------|------|--------|--------|--------|
| 0 | 60 | `$403C` | `04` | 00 | NOP | 0 | 1 | 0 | 0 | R0 → bus |
| 1 | 61 | `$403D` | `01` | 00 | NOP | 0 | 0 | 0 | 1 | Write bus to **abs16** operand |

3-byte insn: `op, addr_lo, addr_hi`. Used by Boot ROM block-copy ([boot-jmp-handoff.md](boot-jmp-handoff.md)).

---

## 4. ALU opcode map (CW B7–B4)

Maps to [alu8](hw/netlist/blocks/alu8.md) `alu_sel`:

| ALU_OP | Operation |
|--------|-----------|
| 0 | NOP |
| 1 | ADD |
| 2 | SUB |
| … | See alu-opcodes-timing.md |

**CMP:** Y follows SUB datapath; **Z** = (`Y==0`), **C_GE** = `net_c_hi` (`net_cmp_z`, `net_cmp_c_ge`) — see [alu8.md](../hw/netlist/blocks/alu8.md).

**2 MHz Execute comb budget:** worst-case ALU Y **151 ns** (SUB/CMP/DEC); ADD/INC **108 ns** @ max ([alu-opcodes-timing.md](alu-opcodes-timing.md) v1.3). ADD micro-sequence ph0–2 must complete operand→Y within **250 ns** half-period before 574 latch.

---

## Change log

| Date | Note |
|------|------|
| 2026-06-02 | BEQ ph0 `Y_OE=0` (`20`); CMP `0x0D` packed (`B0`×2); `cmp_y_oe_bus` hwsim |
| 2026-06-01 | 8b CW; external 574 GPR |
| 2026-06-01 | §3 full packed table (ADD–HALT); CALL/RET/LDIO/STIO draft |
