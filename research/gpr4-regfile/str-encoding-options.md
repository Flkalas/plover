# STR encoding options

**Status:** Research — **no normative pick yet** (per session decision)  
**Parent:** [proposal.md](proposal.md) · Hardware coupling: [pin-budget.md](pin-budget.md)

STR = **store register to memory** at **addr8** with **selectable source register** (not fixed R0 like v1.0 STA).

---

## Evaluation criteria

| Criterion | Weight |
|-----------|--------|
| Instruction size (ROM bytes) | High — affects Fibonacci unroll |
| CU FSM rows / idx5 slots | Medium |
| DP / G-IC wire count | **High** — pin budget |
| Compiler / assembler churn | Medium |
| Boot / legacy STA compatibility | Medium |
| Fibonacci step savings | Illustrative |

---

## Option A — STR0..STR3 (dedicated opcodes)

| Property | Value |
|----------|-------|
| **Encoding** | Four opcodes; `src = opcode[1:0]`; `dst` = addr8 in byte 2 |
| **Size** | **2 bytes** (same as STA) |
| **Example** | `STR2 addr` — store **R2** to `addr` |
| **Opcode candidates** | `0x0C` base (reserved) → `0x0C`=STR0, `0x1A`..`0x1D`, or `0x10\|src` with `opc[4:1]` pattern |

### CU / DP

- During MEM_ST ph0: assert `Y_OE`; set **`r_sel_a = src`** (or internal store mux) so selected reg drives bus.
- If ALU reads stay fixed (P2), only store phase needs select — **fits existing `src[1:0]` wires** during `Y_OE`.

### Pros

- Fixed 2-byte form; easy assembler (`str r2, fa`).
- Fibonacci: replace `TFR02; STA fb` with **`STR2 fb`** (−1 insn/step).
- Opcode embeds src → **no extra G-IC pins** if `src[1:0]` reused.

### Cons

- Four opcodes consume idx5 rows (× phases each).
- R3 needs **STR3** — fourth opcode or extension nibble.
- v1.0 **STA** remains R0-only or aliased to STR0 for compatibility.

### Fibonacci

```text
LDA fa; ADD #bb
LDA fb; STA fa
STR2 fb          ; was TFR02; STA fb
```

---

## Option B — STR with src in operand byte

| Property | Value |
|----------|-------|
| **Encoding** | byte0: STR opcode; byte1: `addr8`; byte2: `src[1:0]` in low bits |
| **Size** | **3 bytes** |

### CU / DP

- Extra fetch phase or wider MBR latch for src field.
- May need **additional FSM phase** for operand fetch → macro stretch.

### Pros

- One opcode mnemonic; arbitrary future fields in byte 3.
- Extends to 4+ regs without more opcode holes.

### Cons

- **+1 byte per store** vs STA — hurts unrolled Fibonacci.
- Longer macro — timing vs 250 ns phase budget needs check.
- More idx5 slots if 4-phase macro.

### Fibonacci

Larger ROM than Option A; not preferred for tight loops.

---

## Option C — STA semantic extension (`r_sel_a` during Y_OE)

| Property | Value |
|----------|-------|
| **Encoding** | Keep **`0x03` STA** opcode; **implicit R0** OR **prior phase latched `r_sel_st`** |
| **Size** | **2 bytes** |

### Variants

| C1 | STA always R0 (v1.0 compat); new **STR*** opcodes for non-R0 |
| C2 | STA becomes alias of STR0; assembler emits STRn |
| C3 | Hidden CU state: last ADD leaves `r_sel_st=R2` auto for next STA |

### CU / DP

- C3 avoids opcode proliferation but **breaks composability** (hidden state).
- C1 is pragmatic **P2** match: minimal wire change.

### Pros

- Boot code using STA unchanged (C1).
- 2-byte stores preserved.

### Cons

- C3 is fragile for compiler.
- “STA” name misleading if src ≠ R0.

---

## Option D — TFR + STA only (no STR)

| Property | Value |
|----------|-------|
| **Encoding** | v1.0 unchanged |
| **Size** | 1 + 2 bytes for TFR+STA |

### Pros

- **Zero ISA change**; no STR research pick needed.
- DP pins unchanged.

### Cons

- Does not meet user goal (store from R2 without move).
- Fibonacci keeps `TFR02` per step.

**Use as baseline** in comparison tables.

---

## Option E — Generalized TFR bit-field (4-reg)

| Property | Value |
|----------|-------|
| **Encoding** | Extend `0x10–0x1F`: `opc[3:2]=dst`, `opc[1:0]=src`, dst/src ∈ {0..3} |
| **Size** | 1 byte implied |

### Note

- Solves **register-to-register** moves, **not** store-to-memory.
- Still need STR or STA for memory.
- 4×4 = 16 pairs; only 12 valid (src≠dst) — fits in 16 opcode slots with `opc[4]=1`.

---

## Comparison table

| Option | Size | Extra G-IC (P2) | idx5 pressure | Fibonacci/step | Compiler |
|--------|-----:|----------------|---------------|----------------|----------|
| **A STR0..3** | 2 B | **0** (reuse `src`) | Medium | **3 insns** (−1) | New mnemonics |
| **B 3-byte STR** | 3 B | 0–2 | High | 3 insns, +1 B each | Flexible |
| **C STA extend** | 2 B | 0–2 | Low–Med | Depends on variant | Compat risk |
| **D no STR** | 3 B | 0 | None | 4 insns | v1.0 |
| **E 4-reg TFR** | 1 B | TFR path | Medium | Still needs STA/STR | TFR table ×4 |

---

## Pin-budget coupling

| Option | Best hardware path |
|--------|-------------------|
| A, C1 | **P2** — `src[1:0]` valid during `Y_OE` only; fixed `q_a/q_b` for ALU |
| A + full `r_sel` ALU | **P0** — fails pins unless P1 mux |
| B | Same as A for DP; CU phase cost dominates |
| D | **rev G** — no change |

**Research lean (non-binding):** For **2×1504 BOM unchanged**, **Option A (STR0..3)** paired with **P2** (fixed ALU reads, store mux via `src[1:0]`) is the **lowest-pin** way to drop Fibonacci TFR. Full 4-GPR ALU flexibility still needs P1/P3/P4.

---

## Boot handoff

[boot-jmp-handoff.md](../../reference/boot/boot-jmp-handoff.md) uses **LDA + MOV** language for GPR init — v1.0 has no MOV. Boot may continue **LDA/STA** to RAM cells for all logical registers. STR opcodes in kernel code require **assembler + JED** bump together; boot ROM can stay STA-only if STR0 ≡ STA(R0).

---

## Decision record

| Date | Action |
|------|--------|
| 2026-07-07 | Document A–E; **defer** normative pick |

Next step: pick after P1/P2 pin proof or WinCUPL spike on P2 STR path.
