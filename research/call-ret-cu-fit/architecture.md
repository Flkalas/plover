# CALL/RET — CPLD-CU architecture (research)

Normative opcode semantics: [microcode-spec.md](../../reference/hardware/microcode-spec.md) §2.3.

## Block diagram

```text
                    ┌─────────────────────────────────────┐
  IR OPC[4:0] ─────►│ idx5 LUT (22 active rows)           │
  phase[1:0]  ─────►│  +24 CALL  +28 RET                │
  FLG_Z       ─────►│  lut_pc_load / lut_pc_flg_z         │
                    └──────────┬──────────────────────────┘
                               │ macro_end
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
        PC_LOAD_EN        MEM_RD/WR         stack FSM
              │           net_addr mux          │
              │                │                │
              ▼                ▼                ▼
        PC 574/161 ◄── PC_in mux ◄── RP latch ($0F00)
              │           (RET≠MBR)      stack $F600+
              └──────────────────────────────────────┘
```

## Sequencer extensions

### CALL @ macro_end (visible phase 0, idx5 24)

1. Latch **return_pc** = PC after 3-byte insn (glue already advanced fetch).
2. Read RP from `$0F00` (16-bit LE) into internal latch.
3. `MEM_WR` × 2 — write return_pc low/high at `mem[RP]`, `mem[RP+1]`.
4. RP ← RP + 2; write RP back to `$0F00`.
5. Assert `PC_LOAD_EN`; **PC_in ← abs16** from MBR (same as JMP).

### RET @ macro_end (visible phase 0, idx5 28)

1. Read RP from `$0F00`.
2. RP ← RP − 2; fault if RP ≤ `$F600`.
3. `MEM_RD` × 2 — read return PC from `mem[RP]`, `mem[RP+1]` into **PC_in latch**.
4. Write RP back to `$0F00`.
5. Assert `PC_LOAD_EN`; **PC_in ← popped word** (not MBR).

### PC_in mux (internal to CU)

| Opcode class | `PC_in` source |
|--------------|----------------|
| JMP, CALL | MBR abs16 latch |
| RET | stack pop latch |
| BEQ (taken) | MBR abs16 latch |

**Target:** no additional SoC output pins — mux inside CU before existing `PC_LOAD_EN` path.

## Reuse vs new logic

| Function | Reuse | New |
|----------|-------|-----|
| idx5 decode | existing `(opcode<<2)\|phase` | 2 LUT rows (minimal) |
| `MEM_RD` / `MEM_WR` | existing strobes | stack FSM asserts during macro_end sub-cycle |
| Address bus | existing `net_addr` glue | internal **addr latch** for RP / stack (no new pins) |
| Branch | `PC_LOAD_EN` + `lut_pc_flg_z` | RET uses same unconditional row as JMP/CALL |
| Fault | — | compare RP vs `$F600` / `$FEEF` → **halt FF** |

## Timing note

Stack assist may require **multiple execute halves** inside one macro_end window, or stretch macro_end across 2+ FSM micro-steps. Cross-check [alu-opcodes-timing.md](../../reference/hardware/alu-opcodes-timing.md) and [M3b-fetch-execute.md](../../reference/hw-bringup/M3b-fetch-execute.md) — if 2-cycle macro_end is required, document on breadboard scope checklist only (behavior unchanged).
