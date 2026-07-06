# Architecture delta — 4-GPR vs v1.0 rev G

**Parent:** [proposal.md](proposal.md) · Baseline: [baseline-rev-g.md](baseline-rev-g.md)

---

## 1. Design rules that break

| # | rev G rule ([cpld-system-controller.md](../../reference/hardware/cpld-system-controller.md)) | 4-GPR proposal |
|---|----------------------------|----------------|
| 1 | **Fixed ALU read:** `q_a←R0`, `q_b←R1` | **Selectable** `r_sel_a`, `r_sel_b` → 4:1 muxes |
| 2 | `w_sel` 3-way (R0–R2) | **4-way** (R0–R3) |
| 7 | TFR via six opcodes + `tfr_valid`/`src` | Optional **unified reg write**; TFR may be redundant |
| — | STA sources R0 only | **STR** sources any GPR |

---

## 2. CPLD-DP (datapath)

### Storage

| | rev G | 4-GPR |
|---|------|-------|
| FF count | 24 (R0–R2) | **32** (R0–R3) |
| `q_a` | `r0*` direct | `mux4(r_sel_a, r0..r3)` |
| `q_b` | `r1*` direct | `mux4(r_sel_b, r0..r3)` |
| Write data | `tfr_valid ? xfer(src) : d_in` | Same structure; **4:1** xfer mux |
| `we_r*` | 3 decode terms | **4** decode terms |

### G-IC

| | rev G | P0 |
|---|------|-----|
| Wires | 6 | **10** (if `r_sel_a/b` added naively) |
| DP I/O | 31/32 | **35/32 FAIL** |

See [pin-budget.md](pin-budget.md).

### PLD equation change (conceptual)

```text
# rev G
q_a0 = r00;

# 4-GPR
q_a0 = !rsa1 & !rsa0 & r00 # !rsa1 & rsa0 & r10 # rsa1 & !rsa0 & r20 # rsa1 & rsa0 & r30;
```

(`rsa0/1` = `r_sel_a`.)

---

## 3. CPLD-CU (control)

### idx5 FSM

Key unchanged: `(opcode[4:0] << 2) | phase[1:0]` — **128 slots**.

**LUT changes per opcode template:**

| Template | rev G strobes (GPR-related) | 4-GPR additions |
|----------|----------------------------|-----------------|
| MEM_LD (LDA) | ph1: `reg_we`, `w_sel=R0` | `w_sel` may target R0–R3 if ISA allows |
| MEM_ST (STA) | ph0: `Y_OE` (R0 via fixed `q_a`) | **STR:** drive `r_sel_a` or dedicated `r_sel_st` during `Y_OE` |
| ALU_REG (ADD) | ph1: `w_sel=R1`; ph2: `w_sel=R2` | ph0–2: program **`r_sel_a`**, **`r_sel_b`** per phase |
| XFER (TFR) | ph0: `tfr_valid`, `src`, `w_sel=dst` | May fold into generic write row |
| CMP | R0 vs imm in R1 | `r_sel` if operands generalized |

### TFR decode block

rev G: six 5-bit opcode minterms OR’d to `tfr_valid`.

4-GPR options:

1. **Keep TFR opcodes** — extend bit-field to dst/src ∈ {0..3} (more opcode space in `0x10–0x1F`).
2. **Drop TFR** — use `MOV`-style implied write via bus or internal mux only in microcode (not user ISA).
3. **Subset TFR** — keep ring moves only; cold transfers via STR/LDA.

CU MC impact: [mc-estimate.md](mc-estimate.md) (~29–40 desk).

---

## 4. ISA / microcode

### Register model

| | v1.0 | v1.1+ candidate |
|---|------|-----------------|
| Architectural GPR | R0, R1, R2 (3fixed) | **R0–R3** |
| ADD result reg | Fixed R2 | Configurable via `w_sel` |
| Store source | Fixed R0 | **STR** with src select |
| TFR | 6 implied opcodes | Optional / generalized |

### Opcode space

| Resource | Notes |
|----------|-------|
| `0x0C` | Reserved (was MOV) — candidate for **STR family** base |
| `0x10–0x1F` | TFR today — could encode **4-reg TFR** or STR0..3 |
| idx5 slots | New opcodes need new FSM rows; 128 slots may be tight if many 3-phase macros added |

### `dec_cpld_seq` axis

[microcode-spec.md](../../reference/hardware/microcode-spec.md) lists **`cpld_dual`** with **R0→A, R1→B**. A 4-GPR promotion changes the architecture row to **`cpld_dual_4gpr`** or bumps ISA minor version.

---

## 5. Software / compiler

[compiler-isa-audit-v1.0.md](../../reference/software/compiler-isa-audit-v1.0.md):

- **GPR 4개:** v1.0 **부분** (하드 3, ISA 제한).
- 4-GPR + STR closes gap for **allocatable registers** and graph-coloring style workloads.

Boot: [boot-jmp-handoff.md](../../reference/boot/boot-jmp-handoff.md) mentions **R0–R3** in comments — likely **software convention** for future 4-reg; v1.0 hardware only implements R0–R2. Research should note **boot ROM** may preset four zero values without R3 existing in silicon.

---

## 6. cyclesim (future implementation map)

| File | Change |
|------|--------|
| `blocks/cpld/dp.py` | `regs[4]`; mux `qa()`/`qb()` from `r_sel_a/b`; `w_sel==3` |
| `blocks/cpld/gic.py` | Extend `GicStrobes` with `r_sel_a`, `r_sel_b`; merge policy |
| `data/fsm_table.py` | Per-phase `r_sel_*` columns; STR template |
| `data/isa.py` | STR opcodes; optional 4-reg TFR decode |
| `tests/test_cpld_dual.py` | 4-reg read/write/mux cases |
| `tests/test_cpu_m3b.py` | Fibonacci without TFR if STR R2 |

**Out of scope** for this research folder — listed for promotion checklist.

---

## 7. Fibonacci example (v1.0 vs STR)

### v1.0 (current `rom_builder.py`)

Per step (a, b → new_a=b, new_b=a+b):

1. `LDA fa; ADD #b` → R2 = a+b  
2. `LDA fb; STA fa` → new_a = b  
3. **`TFR02`; `STA fb`** → R2→R0 then store (STA requires R0)

`TFR02` exists because **STA only drives from R0** (`q_a`), not because ALU writes memory.

### With STR R2 (hypothetical)

```text
LDA fa; ADD #bb     ; R2 = a+b
LDA fb; STA fa      ; new_a = b
STR2 fb             ; store R2 directly — no TFR
```

Saves **1 byte + 1 macro per iteration** if STR encoding is 2-byte imm8 form.

### With full `r_sel` ADD

Could target result in R1 or R3 to avoid R2 convention — requires **ISA + FSM** policy, not DP alone.

---

## 8. Promotion checklist (reference/**)

When (if) moving from research to normative:

1. Update `cpld-system-controller.md` port lists and design rules.
2. Update `microcode-spec.md` §2 (formats, STA/STR, TFR).
3. Update `system-architecture.md` CPU row (3×GPR → 4×GPR).
4. WinCUPL **Design fits** on chosen path (P1/P2/P3/P4).
5. cyclesim + bring-up M2b/M3a docs.
6. Whitepaper §6 ISA narrative.

**None of the above in this work unit.**
