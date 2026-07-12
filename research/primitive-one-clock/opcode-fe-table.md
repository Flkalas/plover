# FE2 opcode F/E timing sheet (desk draft)

**Status:** Research draft — **not** normative  
**Parent:** [SUMMARY-REPORT.md](SUMMARY-REPORT.md) · [programmer-model.md](programmer-model.md)  
**ISA bytes:** [microcode-spec.md](../../reference/hardware/microcode-spec.md) §2

## Policy: optimistic baseline, stretch on fail

1. **Baseline numbers below are optimistic** — pack as much real DP work as plausible into **one E** per insn class.
2. **Lab first at low SYS** (e.g. well below 2 MHz). If a path is **still unstable**, do **not** keep wishing — **add E phases** (split strobes) and update this sheet. That stretch is the recommended fix, not “hope the clock.”
3. Stretch E is still **programmer-visible** (no idle padding, no hidden CU time).

```text
default:  optimistic F/E (this table)
if lab fail @ low clock:  E := E + 1 (or split named strobes)  → re-measure
```

## Rules (FE2)

1. **F** = one SYS to put **PC on the bus** and latch **one** instruction byte (8-bit bus).
2. **E** = one SYS with a **real** datapath strobe window. **No idle E.**
3. Multi-byte insn → **F = byte count** (visible).
4. Gi1 ADD/CMP idle ph0–1 → **deleted**.
5. CALL/RET stack → **listed E slots** (may still be multi-E; merge only where optimistic and lab-backed).

```text
SYS_total = F + E
```

## Core opcode table (optimistic baseline)

| Op | Mnemonic | Bytes | F | E | SYS | E breakdown (optimistic) | Stretch if lab fails |
|----|----------|------:|--:|--:|----:|--------------------------|----------------------|
| `01` | ADD | 2 | 2 | 1 | **3** | E0: ALU ADD + Y_OE + REG_WE + FLG_WE | Split FLG / REG if setup fails |
| `02` | LDA | 2 | 2 | 1 | **3** | E0: MEM_RD + REG_WE→R0 **same SYS** | E0 MEM_RD; E1 REG_WE → SYS **4** |
| `03` | STA | 2 | 2 | 1 | **3** | E0: Y_OE + MEM_WR **same SYS** | E0 Y_OE; E1 MEM_WR → SYS **4** |
| `04` | BEQ | 3 | 3 | 1 | **4** | E0: ALU SUB→FLG + PC_LOAD if Z | E0 ALU; E1 PC_LOAD → SYS **5** |
| `05` | JMP | 3 | 3 | 1 | **4** | E0: PC_LOAD←abs16 | (rarely needs split) |
| `06` | CALL | 3 | 3 | 3 | **6** | E0: WR ret_lo; E1: WR ret_hi+RP+=2; E2: PC_LOAD | If unstable: E=4 (separate RP / PC) → SYS **7** |
| `07` | RET | 1 | 1 | 2 | **3** | E0: RP-=2 + MEM_RD lo; E1: MEM_RD hi + PC_LOAD | E=3 fully split → SYS **4** |
| `08` | LDIO | 2 | 2 | 1 | **3** | same as LDA (MMIO) | same stretch as LDA |
| `09` | STIO | 2 | 2 | 1 | **3** | same as STA | same stretch as STA |
| `0A` | HALT | 1 | 1 | 1 | **2** | E0: halt hold | — |
| `0C` | *(reserved)* | — | — | — | — | — | — |
| `0D` | CMP | 2 | 2 | 1 | **3** | E0: ALU CMP + FLG_WE | Split if flags late |
| `0F` | STA16 | 3 | 3 | 1 | **4** | E0: Y_OE + MEM_WR @ abs16 | E0/E1 split → SYS **5** |

`0x10–0x1F`: invalid — no F/E sheet (trap).

## Reading the table

| Class | Optimistic SYS | First stretch |
|-------|---------------:|---------------|
| ALU imm (ADD/CMP) | **3** | keep E=1 usually (path ~133 ns @ 2 MHz) |
| MEM / MMIO imm8 | **3** | **+1 E** if mem→reg (or Y→mem) fails even when clock is low |
| Abs16 JMP/STA16 | **4** | F×3 dominates |
| BEQ | **4** | +1 E if FLG→PC_LOAD late |
| CALL | **6** | +1 E stack/PC |
| RET | **3** | +1 E stack/PC |

## Lab recommendation (short)

1. Bring up FE2 paths at **low SYS** first.
2. If MEM (LDA/STA) or BEQ/CALL still glitches → **increase E** per stretch column; update this table and [cycle_model.py](model/cycle_model.py).
3. Only then raise clock toward 2 MHz. Do not treat “raise clock later” as the fix for a bad single-E packing.

## Walkthrough examples

### ADD `$10` (baseline)

```text
F0  IR = 01
F1  MBR = 10
E0  R0 <- R0 + MBR
total SYS = 3
```

### LDA `$20` (optimistic)

```text
F0  IR = 02
F1  MBR = 20
E0  MEM_RD @ $0020  and  REG_WE -> R0
total SYS = 3
```

### LDA `$20` (stretch after lab fail)

```text
F0  IR = 02
F1  MBR = 20
E0  MEM_RD @ $0020
E1  REG_WE -> R0
total SYS = 4
```

### CALL `$1234` (optimistic)

```text
F0..F2  opcode + abs16
E0      mem[RP] <- ret_lo
E1      mem[RP+1] <- ret_hi ; RP += 2
E2      PC <- target
total SYS = 6
```

## Gi1 vs FE2 E (exec)

| Op | Gi1 exec | FE2 E (opt.) | Idle removed? |
|----|---------:|-------------:|---------------|
| ADD/CMP | 3 | 1 | **Yes** |
| LDA/STA | 2 | **1** | packed (stretch back to 2 if needed) |
| JMP | 1 | 1 | n/a |
| CALL/RET | 1+assist | 2–3 | assist **visible** |

## Sync with cycle model

[model/cycle_model.py](model/cycle_model.py) matches this **optimistic** sheet (LDA/STA E=1, BEQ E=1, CALL E=3, RET E=2).

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Optimistic baseline; stretch-E if lab fails at low clock |
| 2026-07-13 | First FE2 opcode F/E draft |
