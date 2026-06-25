# Microcode Specification v1.1b

**Status:** Archived reference — **merged into** [microcode-spec.md](../../hardware/microcode-spec.md).  
**Active normative:** v1.0 — [system-architecture.md](../../hardware/system-architecture.md)  
**Design authority:** [cpu-4axis-arch-search-report.md](../../hardware/cpu-4axis-arch-search-report.md)  
**Search:** `python tools/cpu_arch_search.py --pareto` → `build/cpu_arch_pareto.json` (local, gitignored)  
**Related (archived):** [opcode-expanded-control.md](opcode-expanded-control.md) · [cpld-system-controller-v1.1b.md](cpld-system-controller-v1.1b.md)

---

## 1. Recommended architecture (Pareto winner)

| Axis | Choice | Rationale |
|------|--------|-----------|
| Opcode | **`op_legacy`** (`0x01–0x0F`) | Minimal Flash migration; interpreter unchanged |
| Index | **`idx4`** `(opcode[3:0]<<2)\|phase` | No CW MUX widen on bench |
| Decode | **`dec_cpld_seq`** | Phase FSM in CPLD; no `alu8_decode` |
| CPLD | **`cpld_3fixed`** | R0→A, R1→B, R2=result; ~26 MC |
| CW/Flash | **`cw_hybrid`** | **~25 param rows** vs ~23 per-phase v1.0 |

**Metrics vs v1.0 baseline:** DIP **31→20** (−11), delay **151→136 ns** (−15), Flash **23→25** rows, MC **40→26**.

**Forward paths:**

| ID | When |
|----|------|
| **H1** `op_class` + `cpld_3seq` + `cw_hybrid` | Expanded Forth/DOS opcode families; **28 Flash rows**; MC ~50 |
| **H2** `op_expanded` + `cw16_direct` + `idx8` | Full 8-bit opcode namespace; **140 rows**; simplest cw_direct bring-up |

---

## 2. Hybrid control store (`cw_hybrid`)

### 2.1 Partition

| Source | Content |
|--------|---------|
| **CPLD phase FSM** | Fixed templates: ADD (3 ph), LDA/STA (2 ph), LDIO/STIO, CMP |
| **Flash param row** | Per-opcode **8–16 b** exception: `REG_WSEL`, `branch_arm`, macro length override |
| **Flash full rows** | JMP, BEQ, CALL, RET, HALT, MOV, STA16 — macro boundary / branch glue |

### 2.2 Indexing (recommended `idx4`)

```text
param_index = opcode[7:0]              # one 2-byte slot per opcode (hybrid)
class_index = (opcode[7:4] << 2) | phase   # H1 only
per_phase   = (opcode[3:0] << 2) | phase   # branch macros (legacy)
```

Flash base **`$4000`**, **2 bytes/slot**, **2048 slots** unchanged ([rom-architecture.md](rom-architecture.md)).

### 2.3 Build tools

| Function | Module |
|----------|--------|
| `pack_hybrid_store()` | `tools/pack_control_store.py` |
| `pack_cw16()` | 16-bit direct rows (H2) |
| `legacy_to_cw16()` | Migration helper from v1.0 10-bit CW |

Verify: `python tools/verify_control_store.py` (extend for v1.1b fixtures).

---

## 3. 16-bit control word (`cw16_direct`, H2)

Physical slot: **2 bytes** @ `$4000 + 2×index`. All 16 bits used — **no `ALU_OP` nibble**.

| Bit(s) | Field | Drives |
|--------|-------|--------|
| 15–14 | `REG_WSEL[1:0]` | CPLD write target (R0–R2) |
| 13 | `y_mux_sel` | 157 arithmetic vs logic Y |
| 12–9 | `lgc3:0` | 153_L logic |
| 8 | `cin` | 283 C0 |
| 7 | `b_sel` | 153_B mux |
| 6 | `b_const_sel` | INC/DEC constant |
| 5 | `flags_only` | CMP / BEQ flag path |
| 4 | `REG_WE` | CPLD write |
| 3 | `Y_OE` | Bus drive |
| 2 | `MEM_RD` | Memory read |
| 1 | `MEM_WR` | Memory write |
| 0 | reserved | 0 |

**Timing:** hwsim spot tests `hw/tests/cpu_cw_direct_sub.yaml`, `cpu_cw_direct_add.yaml` — path ≤ **250 ns** @ 2 MHz Execute.

---

## 4. Macro ISA

v1.0 mnemonics **`0x01–0x0F`** retained. Operand byte follows opcode.  
`MOV` (`0x0C`) deprecated in H1/H2 — use fixed-reg copy opcodes per [opcode-expanded-control.md](opcode-expanded-control.md) §4.

Phase counts for CPLD FSM (same as v1.0):

| Op | Phases | Sequencer |
|----|--------|-----------|
| ADD | 3 | CPLD template |
| LDA, STA, LDIO, STIO, STA16 | 2 | CPLD template |
| CMP | 3 | CPLD template |
| BEQ, JMP, CALL, RET, HALT, MOV | 1–2 | Flash rows + branch sample @ macro end |

---

## 5. Migration from v1.0

| Step | Action |
|------|--------|
| P1 | Strap `DECODE_BYPASS`; program hybrid param + branch rows |
| P2 | Fit CPLD `cpld_3fixed` + phase FSM; drop `alu8_decode` netlist |
| P3 | Optional H2: widen CW index to 10b, `pack_cw16` full store |
| P4 | Optional H1: `op_class` namespace + class param rows |

**Do not migrate** CE/mailbox into CPLD — **138×2 + glue** stays off-chip.

---

## 6. hwsim acceptance

| Test | Purpose |
|------|---------|
| `cpu_cw_direct_sub.yaml` | SUB critical path, no decode |
| `cpu_cw_direct_add.yaml` | ADD execute |
| `cpld_seq_add.yaml` | 3-phase ADD @ 250 ns boundaries |
