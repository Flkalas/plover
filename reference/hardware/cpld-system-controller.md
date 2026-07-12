# CPLD System Controller v1.0 P12

**Devices:** 2× **ATF1504AS-10JU44** (PLCC-44)  
**Roles:** **CPLD-CU** — **pipe FSM** (see [cpld-pipe-cu.md](cpld-pipe-cu.md)) + direct strobes + branch · **CPLD-DP** — **R0 (AC) only** + `q_a`  
**CE tree:** 74HC138×2 + 08/32/04 (off-chip)

**Related:** [control-and-decode.md](control-and-decode.md) · [cpld-dual-routing.md](cpld-dual-routing.md) · [cpld-dual-jtag.md](cpld-dual-jtag.md) · [microcode-spec.md](microcode-spec.md)

**Bitstream:** Pipe CU **Design fits pending**. DP is **R0-only** PLD (`q_a`).

---

## 1. Design rules

1. **ALU A:** `q_a` ← **R0** only (CPLD-DP).
2. **ALU B:** **`net_mbr[7:0]`** (MBR / oper latch) → `net_b[7:0]`.
3. **Write target:** **`reg_we` → R0** only (G-IC is one wire).
4. **Pipe FSM** on CPLD-CU — [cpld-pipe-cu.md](cpld-pipe-cu.md).
5. **Strobes:** CU drives memory/ALU/PC nets directly to SoC.
6. **Branch:** `PC_LOAD_EN` with taken **BRANCH_BUBBLE** (no prediction).
7. **Return stack assist:** CALL/RET in **STACK_EX** — RP `$0F00`, stack RAM via `MEM_RD`/`MEM_WR` ([microcode-spec.md](microcode-spec.md) §2.3 · [cpld-pipe-cu.md](cpld-pipe-cu.md) §5.1).
8. **Opcodes `0x10–0x1F`:** reserved / trap.
9. **Mailbox, MAP, `/CE`** — outside CPLD.

---

## 2. CPLD-CU port list

### Inputs

| Signal | Source | Role |
|--------|--------|------|
| `OPC[4:0]` | IR latch | Pipe decode |
| `FLG_Z` | FLG574 | BEQ |
| `CLK` | 2 MHz `CLK_SYS` | Pipe FSM |
| Stall / port sense | glue or CU | MEM_STALL / FALLBACK |

### Outputs — SoC

| Signal | Function |
|--------|----------|
| `MEM_RD`, `MEM_WR` | Memory strobes |
| `Y_OE` | Bus drive |
| `FLG_WE` | Flag latch write |
| `PC_LOAD_EN` | Branch / redirect commit |
| `cin`, `bctrl0`, `bctrl2`, `lgc0..3`, `s0`, `s1` | ALU controls |
| PROG / IF enables | Program-port isolation |

`bctrl1`/`bctrl3` fan out at 153 from `bctrl0`/`bctrl2`.

### Outputs — G-IC to CPLD-DP (1)

| Signal | Function |
|--------|----------|
| `reg_we` | GPR write (→ R0) |

Full state machine, SYS tax, timing: **[cpld-pipe-cu.md](cpld-pipe-cu.md)**.

---

## 3. CPLD-DP port list

### Inputs (9)

| Signal | Source | Role |
|--------|--------|------|
| `d_in[7:0]` | Data bus | LDA / ALU writeback |
| `reg_we` | CPLD-CU G-IC | R0 write strobe |
| `CLK` | 2 MHz | R0 FF clock |

### Outputs (8)

| Signal | Function |
|--------|----------|
| `q_a[7:0]` | Async read → ALU A |

ALU B comes from **MBR / oper latch** off-chip (`net_mbr` → `net_b`).

**Pin budget (desk):** **17/32** used (15 spare).

---

## 4. G-IC bundle

| ID | Signal | DP pin (desk) |
|----|--------|---------------|
| G01 | `reg_we` | 12 |

**CLK:** pin 43 both chips (parallel).

Detail: [cpld-dual-routing.md](cpld-dual-routing.md)

---

## 5. Extra program state

Additional variables live in **RAM**. Normative visible GPR is **R0** only.

---

## 6. JTAG / programming

Daisy chain: programmer → **CU (TDI first)** → **DP** → programmer TDO.  
TCK/TMS paralleled. See [cpld-dual-jtag.md](cpld-dual-jtag.md).

---

## 7. EX policy (P12 pipe)

ADD/CMP use **packed EX**. MBR/oper hold during ALU EX. MEM ops use **MEM_STALL**. Detail: [cpld-pipe-cu.md](cpld-pipe-cu.md).

### PC load path

| Op | `PC_in` source @ `PC_LOAD_EN` |
|----|-------------------------------|
| JMP, CALL, BEQ | abs16 from operand latch |
| RET | **popped 16-bit return address** (not MBR) |

---

## 8. MC / fit gate

| Chip | Gate |
|------|------|
| CPLD-CU (pipe) | WinCUPL **Design fits** when `.pld` exists |
| CPLD-DP | WinCUPL Design fits |

Do not record fitter used-MC counts as normative BOM gates.
