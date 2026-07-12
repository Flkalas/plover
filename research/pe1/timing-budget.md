# PE1 timing / clock budget (desk)

**Status:** Research (non-normative)  
**Build:** PE1 · [architecture.md](architecture.md) · [SUMMARY-REPORT.md](SUMMARY-REPORT.md)  
**Frozen Gi1 numbers:** [cpld-dual-timing.md](../../reference/hardware/cpld-dual-timing.md) · [alu-opcodes-timing.md](../../reference/hardware/alu-opcodes-timing.md)

## Clock assumptions

| Item | Value | Note |
|------|------:|------|
| `CLK_SYS` (desk) | **2.0 MHz** | Same crystal/÷2 story as Gi1 BOM |
| Period `T` | **500 ns** | posedge → next posedge |
| Gi1 execute half | **250 ns** | historical φ_exec budget |
| PE1 primary budget | **500 ns** | IF and EX each close to next SYS edge (full cycle) |
| PE1 stress check | **250 ns** | If PE1 keeps Gi1-style half-cycle latching |

IF and EX run **in parallel** on one SYS edge. Slack is computed **per path**, not IF+EX summed into one series chain.

```text
slack = budget_ns - path_ns
```

Parts (datasheet-class desk):

| Part | Delay used (ns) | Role |
|------|----------------:|------|
| SST39SF010A-70 | **70** | PROG `t_ACC` (Flash) |
| IS62C256 ~45 | **45** | DATA SRAM access |
| 74HC245 | **15** | bus buffer typ/desk |
| 74HC157 mux | **15** | addr select |
| 74HC574 setup | **20** | IR / PC / ACC class (desk, near Gi1 28 max setup band) |
| 74HC574 clk→Q | **20** | PC/IR launch |
| CPLD async / decode | **15** | CU pipe/stall (desk) |
| wire | **10** | breadboard |

Gi1 frozen comb paths reused:

| Path | ns | Source |
|------|---:|--------|
| Gi1 ADD (P8) | **~133** | cpld-dual-timing |
| SUB/CMP Y | **136** | alu-opcodes-timing |
| INC worst Y | **153** | alu-opcodes-timing |
| BEQ merge | **212** | cpld-dual-timing |

## Critical paths (PE1)

### IF — program fetch (opcode or operand byte)

```text
PC.Q → mux → PROG buffer → Flash t_ACC → 245 → IR/oper.D setup
```

| Segment | ns |
|---------|---:|
| PC clk→Q | 20 |
| addr mux | 15 |
| PROG buffer | 15 |
| Flash `t_ACC` | 70 |
| data 245 | 15 |
| IR setup | 20 |
| wire | 10 |
| **IF total** | **165** |

| Budget | Slack |
|--------|------:|
| **500 ns** (primary) | **335 ns** |
| **250 ns** (stress) | **85 ns** |

### EX — ALU ADD (steady stream, imm already in MBR/oper latch)

```text
R0 q_a + oper.B → ALU → Y_OE / REG_WE path (Gi1 P8) + small PE1 mux tax
```

| Segment | ns |
|---------|---:|
| Gi1 ADD P8 | 133 |
| PE1 A-bus/qualify tax | 15 |
| **EX ADD total** | **148** |

| Budget | Slack |
|--------|------:|
| **500 ns** | **352 ns** |
| **250 ns** | **102 ns** |

### EX — BEQ taken (ALU SUB → FLG → PC_LOAD) + squash IF

```text
Gi1 BEQ 212 + CU squash/refetch qualify
```

| Segment | ns |
|---------|---:|
| Gi1 BEQ | 212 |
| pipe squash / IF kill | 15 |
| **EX BEQ total** | **227** |

| Budget | Slack |
|--------|------:|
| **500 ns** | **273 ns** |
| **250 ns** | **23 ns** |

### EX — DATA MEM (LDA-class)

```text
addr mux → SRAM t_ACC → 245 → REG_WE setup
```

| Segment | ns |
|---------|---:|
| addr mux + RP/MBR launch | 35 |
| SRAM | 45 |
| 245 | 15 |
| REG setup / CPLD | 25 |
| wire | 10 |
| **EX MEM total** | **130** |

| Budget | Slack |
|--------|------:|
| **500 ns** | **370 ns** |
| **250 ns** | **120 ns** |

### EX — Mailbox MMIO (`LDIO` / `STIO`, PE1 latch tax)

Normative window `$FF00–$FFFB` ([mailbox-protocol.md](../../reference/copro/mailbox-protocol.md)). Path is **not** main SRAM; RP2350 shadow + LVC245 tap ([rp2354b-board-design.md](../../reference/copro/rp2354b-board-design.md)).

```text
decode MAILBOX_EN → PE1 mux/latch → LVC245 → RP GPIO shadow R/W → 245 → R0/MBR setup
```

| Segment | Desk ns |
|---------|--------:|
| decode / `MAILBOX_EN` | 20 |
| PE1 mux/latch tax | 20 |
| LVC245 A→B | 10 |
| **RP GPIO valid** (assumption — lab gate) | **80** |
| return 245 + CPU setup | 30 |
| wire | 10 |
| **EX mailbox R/W total** | **170** |

| Budget | Slack |
|--------|------:|
| **500 ns** | **330 ns** |
| **250 ns** | **80 ns** |

If measured RP response exceeds ~80 ns, raise the desk number or stretch that EX (same policy as FE2). Mailbox is still **looser than BEQ** at 250 ns (80 vs 23 ns slack).

Job matrix / product conclusion: [mailbox-2mhz.md](mailbox-2mhz.md).

### Overlap check (same SYS)

IF and EX do **not** add. Limiting path on an ADD+fetch tick is `max(IF, EX_ADD)`:

| Combo | max path | Slack @ 500 | Slack @ 250 |
|-------|---------:|------------:|------------:|
| IF + EX ADD | **165** | **335** | **85** |
| IF + EX MEM | **165** | **335** | **85** |
| IF + EX mailbox | **170** | **330** | **80** |
| IF + EX BEQ | **227** | **273** | **23** |

**Desk limiter @ 2 MHz:** **BEQ** on the 250 ns stress budget (**~23 ns** left). **Mailbox is not the limiter** under the 80 ns RP assumption. At full **500 ns**, BEQ still has **~273 ns** slack.

## Implied Fmax (desk, path-limited)

Using `Fmax ≈ 1 / path` for single-edge pipe (period must exceed path):

| Limiting path | path ns | Fmax desk |
|---------------|--------:|----------:|
| IF 165 | 165 | **~6.0 MHz** |
| EX ADD 148 | 148 | **~6.7 MHz** |
| EX BEQ 227 | 227 | **~4.4 MHz** |
| EX mailbox 170 | 170 | **~5.9 MHz** |

PE1 remains at **2.0 MHz** for large margin bring-up. Elevated clocks: see [clock-candidates.md](clock-candidates.md) (**3.6864 MHz** preferred over raw **4.0 MHz**). Measure BEQ slack per [beq-lab.md](beq-lab.md).

## What eats the Gi1 slack

| vs Gi1 | Change |
|--------|--------|
| IF | Flash **70 ns** always on PROG path (was shared-bus fetch, same order) + **extra buffers** (~30 ns) for isolation |
| EX ADD | **+~15 ns** PE1 qualify/mux vs bare Gi1 133 |
| EX BEQ | **+~15 ns** squash; stress half-cycle becomes tight |
| EX mailbox | PE1 latch + LVC245 + **RP GPIO (~80 ns assumed)**; still OK @ 2 MHz |

## Lab recommendation

1. Scope IF Flash→IR and EX ADD Y at **2 MHz**; confirm both finish before the capturing edge.
2. Scope **mailbox `LDIO`**: MEM_RD→D valid from RP before capturing edge; if >80 ns RP, update this sheet.
3. If BEQ fails with half-cycle discipline, either use **full-period** latching or **stretch** BEQ (extra SYS) — same stretch policy as FE2/PE1 bubble tables.
4. Do not raise `f_SYS` until **measured** BEQ slack is **≥ 50 ns** ([beq-lab.md](beq-lab.md)); design margin policy **≥ 20–30%** of 227 ns ([clock-candidates.md](clock-candidates.md)).

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Link clock-candidates + beq-lab; margin ≥50 ns / 20–30% |
| 2026-07-13 | Mailbox EX path + slack vs MEM/BEQ |
| 2026-07-13 | Initial PE1 ns budget / slack desk |
