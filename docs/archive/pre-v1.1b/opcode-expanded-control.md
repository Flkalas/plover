# Opcode-expanded control plane (v1.1b proposal)

**Status:** Archived draft (internal codename v1.1b) — **not normative**.  
**Active normative:** v1.0 — [microcode-spec.md](../../hardware/microcode-spec.md)  
**Goal:** Expand **program opcode space** and **Flash microcode** so combinatorial **74HC decode** (`alu_decode`, BEQ glue, optional `lgc` SOP) can be removed or minimized.  
**Audience:** Interpreter + PL-DOS track (fixed R0/R1/R2, no GPR ISA).  
**Related:** [alu-decode-architecture-study.md](alu-decode-architecture-study.md) · [microcode-spec.md](../../hardware/microcode-spec.md) · [rom-architecture.md](../../hardware/rom-architecture.md) · [compiler-isa-audit-v1.0.md](../../software/compiler-isa-audit-v1.0.md)

---

## 1. Problem (v1.0)

| Block | 74HC role | ~DIP | Opcode / CW relationship |
|-------|-----------|------|---------------------------|
| **`alu8_decode`** | `ALU_OP[3:0]` → `cin`, `b_sel`, `b_const_*`, `lgc3:0`, `y_mux` | **~9** (SOP 37 gates) or **~3** (154+00) | **Same 4-bit `ALU_OP` reused** across many macro ops → needs comb decode |
| **BEQ glue** | `FLG.Z` ∧ BEQ active → PC load enable | **shared** with CE 08/32 (#11b) | Branch split across CMP micro + glue |
| **CE / mailbox** | A15, MAP, `$FF00` window | **138×2 + 08/32/04** | **Not removable** via opcode (needs address pins) |

v1.0 already stores **micro-sequences in Flash** (`$4000+`), but **ALU datapath controls are still compressed into `ALU_OP`** and expanded by `alu_decode` on the breadboard ([hardware-architecture-synthesis.md](hardware-architecture-synthesis.md) §4.1).

**Insight:** Flash has **4096 B** CW region and **sparse** slot use; comb decode exists to save CW bits, not because Flash is full.

---

## 2. Strategy: “fat microcode, thin hardware”

```text
v1.0:  Flash CW (10b) ──► ALU_OP[3:0] ──► alu_decode (74HC) ──► ALU controls
v1.1b: Flash CW (16b) ──► ALU controls DIRECT ──► ALU (no alu_decode)
       Program opcode (8b) ──► wider store index ──► one row per primitive
```

Three coupled changes:

1. **`cw_direct`** — CW carries **raw** `cin`, `b_sel`, `b_const_sel`, `lgc3:0`, `y_mux_sel` (no `ALU_OP` decode chip).
2. **Opcode index 8-bit** — `store_index = (opcode[7:0] << 2) | phase[1:0]` (1024 slots; fits 2048×2 B Flash).
3. **Fixed 3 registers** — `REG_SEL` often **implicit per opcode** in Flash; CPLD read path **R0→A, R1→B** hardwired.

---

## 3. 16-bit control word (per micro-phase)

Physical slot remains **2 bytes** at `$4000 + 2×index` ([rom-architecture.md](rom-architecture.md)); v1.0 used 10 bits. **Proposal: use all 16.**

| Bit(s) | Field | Drives |
|--------|-------|--------|
| 15–14 | `REG_WSEL[1:0]` | CPLD write target (R0–R2); read **fixed** |
| 13 | `y_mux_sel` | 157: arithmetic Y vs logic Y |
| 12–9 | `lgc3:0` | 153_L Gigatron logic (or tie-off if `y_mux_sel=0`) |
| 8 | `cin` | 283 C0 |
| 7 | `b_sel` | 153_B: B vs ~B |
| 6 | `b_const_sel` | 153_B: INC/DEC constant |
| 5 | `cmp_n` / `flags_only` | CMP: suppress misleading bus drive (legacy `Y_OE=0` semantics) |
| 4 | `REG_WE` | CPLD latch write |
| 3 | `Y_OE` | ALU Y → bus |
| 2 | `MEM_RD` | Memory read |
| 1 | `MEM_WR` | Memory write |
| 0 | `reserved` | tie 0 |

**Build:** extend `tools/pack_control_store.py` → `pack_cw16(...)`; verify with hwsim **direct** control nets (no `alu8_decode` block in path).

**Timing:** Same 2 MHz Execute half-period; removing decode chain **adds slack** (~17–46 ns per [alu-opcodes-timing.md](alu-opcodes-timing.md)).

---

## 4. Opcode map (interpreter-first)

### 4.1 Indexing

```text
store_index = (IR[7:0] << 2) | phase[1:0]    # 10-bit index → 1024 rows
CW_addr     = $4000 + 2 * store_index
```

Hardware: widen CW address MUX from **6** to **10** bits (161 cascade or 2×574 preset). Flash **2048 slots** still sufficient.

### 4.2 Namespace (draft)

| Range | Use | Replaces comb logic |
|-------|-----|---------------------|
| `0x00` | `NOP` / padding | — |
| `0x01–0x0F` | **v1.0 compat** aliases (same mnemonics, fatter CW rows) | `alu_decode` for these rows only if legacy mode |
| `0x10–0x1F` | **ALU immediate** — `ADDI_R0`, `SUBI_R0`, `ANDI`, … one opcode each | No shared `ALU_OP` decode |
| `0x20–0x2F` | **Memory** — `LDA_R0`, `STA_R0`, `STA16_R0`, `LDIO`, `STIO` | Fixed target reg in CW |
| `0x30–0x3F` | **Branch** — `BEQ`, `BNE`, `BCS`, `JMP`, `CALL`, `RET` | BEQ glue → macro FSM / last-phase CW |
| `0x40–0x5F` | **Forth primitives** — `@`, `!`, `DUP`, `DROP`, `+`, … | Each = 1–4 phased CW strip |
| `0x60–0x7F` | **Kernel / DOS** — `VFDD_READ`, `VFDD_WRITE`, `VDU_PUT` stubs | MMIO sequences in Flash |
| `0x80–0xFF` | Reserved / user colon defs (interpreter compiles to calls) | — |

**`MOV` with `(dst<<4)|src` eliminated** — fixed 3-reg: use `LDA`/`STA`/dedicated copy opcode (`0x12` `COPY_R1_R0`, etc.).

### 4.3 Example: `ADDI_R0` (`0x10`)

Program: `10 imm8` (2 bytes). Micro-phases (CW pre-packed, **no decode**):

| ph | `cin` | `b_sel` | `b_const` | `lgc` | `y_mux` | `REG_WE` | `REG_WSEL` | Action |
|----|-------|---------|-----------|-------|---------|----------|------------|--------|
| 0 | 0 | 0 | 0 | AND | 0 | 0 | — | R0→A (fixed read) |
| 1 | 0 | 0 | 0 | PASS | 0 | 0 | — | imm→B (bus/MBR path) |
| 2 | 0 | 0 | 0 | ADD | 0 | 1 | 0 | Y→R0 |

---

## 5. 74HC removal budget

| Item | Action | Est. DIP saved | Stays on breadboard |
|------|--------|----------------|---------------------|
| **`alu8_decode` SOP** | Remove; `cw_direct` | **~9** (04/08/32 used only by decode netlist) | ALU datapath 153/283/157/04 (B-path) |
| **`hc154` path** | Not adopted if `cw_direct` | ~3 | — |
| **`lgc_direct` local OR** | `y_mux_sel` in CW | **~1** (32) | — |
| **BEQ glue** | Macro sequencer samples `FLG` @ macro end; `BEQ`/`BNE`/`BCS` distinct opcodes | **~0.5–1** (partial 08/32) | FLG 574 + 161 PC |
| **CE / mailbox** | No change | 0 | **138×2 + 08/32/04** |
| **Addr MUX** | Wider CW index | +1 161 or 574 tap | 157 PC path |

**Net:** **~10–11 DIP** from control decode if `alu8_decode` is fully dropped and BEQ glue simplified. **CE tree unchanged.**

**Risk:** More Flash programming discipline; wrong CW row = wrong control (same as today, but more bits to edit).

---

## 6. Branch without BEQ glue (sketch)

v1.0: BEQ phase 0 runs SUB flags; phase 1 + **08/32** gates PC←operand if Z.

v1.1b options (pick one in bring-up):

| Option | Hardware | Software |
|--------|----------|----------|
| **A. Macro boundary** (preferred) | IR=`BEQ` after micro done; **sequencer** (161+glue **2 gates**) loads PC if `FLG.Z` | Match `plover_vm` `MacroEngine._apply_macro_side_effects` |
| **B. Prior insn** | Separate `CMP` / `TST` opcode; `BEQ` only tests FLG | 2-byte compare + 3-byte branch |
| **C. CW `branch_arm` bit** | Last phase sets latch; AND with Z | Flash packs branch row |

Option A removes **wide** BEQ random glue but keeps **minimal** Z test at macro end — not zero gates unless sequencer is microcoded (state in Flash + counter).

---

## 7. Migration phases

| Phase | Deliverable | v1.0 breadboard |
|-------|-------------|-----------------|
| **P0** | This doc + `pack_cw16` prototype in `tools/` | — |
| **P1** | `cw_direct` for **existing** `0x01` ADD / `0x0D` CMP rows; **bypass `alu8_decode`** on bench | Dual-mode: strap `DECODE_BYPASS` |
| **P2** | 8-bit `store_index`; CW MUX widen; `plover_asm` / `isa.py` opcode table | Breaking CW addr |
| **P3** | Forth primitive opcode block `0x40+`; drop `MOV` reg nibble | Interpreter asm |
| **P4** | Remove `alu8_decode.yaml` from SoC netlist; update BOM maintenance | −~9 DIP |

**Do not migrate CE/mailbox** into CPLD or opcode — address pins stay **138 + glue** ([memory-map.md](memory-map.md)).

---

## 8. Tooling checklist

- [ ] `tools/pack_control_store.py` — `pack_cw16`, `cw_direct` rows from `alu8_cases` / `default_lgc_direct_arith`
- [ ] `tools/alu_decode_search.py` — score **post-migration** DIP (decode arch = `cw_direct` only)
- [ ] `hw/tests/` — execute path **without** `alu8_decode` instance
- [ ] `docs/hardware/microcode-spec.md` — §16b CW (or `microcode-spec-v1.1b.md`)
- [ ] `docs/hw-bringup/b3-opcode.md` — regenerate for **direct** ties (fewer DIP cheat rows)
- [ ] `plover_vm/micro/cw.py` — `lookup_cw` 16-bit

---

## 9. Relation to other tracks

| Track | Opcode expansion |
|-------|------------------|
| **Interpreter + PL-DOS** | **Primary beneficiary** — Forth words → dedicated opcodes |
| **Subset C / GPR ISA** | Not required; use `0x80+` only if later |
| **v1.1 MMU** | Orthogonal — `/NMI` fault glue stays discrete |

---

## 10. Summary

| Question | Answer |
|----------|--------|
| Opcode 확장으로 74를 줄일 수 있나? | **예 — `alu_decode` (~9 DIP)가 1차 타깃** (`cw_direct`) |
| 8비트 전부 opcode? | **인덱스 8비트**로 가능; operand는 주소/즉값으로 **별도 바이트 유지** |
| CE/mailbox도 opcode로? | **아니오** — 138+glue 유지 |
| 고정 3레지와 함께? | **권장** — `REG_WSEL`만 CW; read MUX 제거 |

**Recommended corner:** **`cw_direct` + 8-bit store index + fixed R0/R1/R2** — matches Pareto winner in [alu-decode-architecture-study.md](alu-decode-architecture-study.md) §4 and interpreter roadmap.

---

## Change log

| Date | Note |
|------|------|
| 2026-06-24 | Initial proposal |
