# Bus / timing feasibility (desk)

**Non-normative.** Numbers from [cpld-dual-timing.md](../../reference/hardware/cpld-dual-timing.md) · [alu-opcodes-timing.md](../../reference/hardware/alu-opcodes-timing.md) · fetch map [M3b-fetch-execute.md](../../reference/hw-bringup/M3b-fetch-execute.md).

**Clock:** normative **2.0 MHz** (period 500 ns, execute half 250 ns).

## Legend

| Tag | Meaning |
|-----|---------|
| **FE1** | fetch+execute in **one** SYS |
| **FE2** | **F** then **E** (no idle); multi-E only if bus needs it |
| **OK** | Fits desk path |
| **NO** | Structural bus/ISA conflict |
| **COND** | Needs ISA/CU contract change or slower clock |

## Critical paths (execute only)

| Path | Desk ns | @ 250 ns half |
|------|--------:|---------------|
| Gi1 ADD (R0+MBR) | ~133 | OK |
| BEQ merge | 212 | OK (tight) |

Execute-only 1 SYS is **not** the FE1 problem. **Bus exclusivity** is.

## Shared-bus conflict (FE1 root cause)

On one A-bus / D-bus:

| Need in same SYS | Conflict |
|------------------|----------|
| PC → fetch opcode | Uses address = PC |
| MEM_RD at MBR address | Needs address = MBR |
| Stack push at RP | Needs yet another address |

Without a second memory port, **FE1 for LDA/STA/CALL is NO**.

Multi-byte insn: abs16 needs **2–3 fetch bytes** before E — cannot be one SYS on an 8-bit bus.

## Per-template matrix

| Template | Bytes | Gi1 exec phases (normative sketch) | FE1 | FE2 |
|----------|------:|------------------------------------:|-----|-----|
| ADD/CMP imm | 2 | 3 (2 idle + 1 ALU) | **NO** (fetch+ALU same tick after 2-byte fetch) / toy COND if imm preloaded | **COND Go** — F gets opcode+imm; E = ALU (drop idle) |
| LDA/STA | 2 | 2 MEM | **NO** (fetch vs data addr) | **COND** — F latch addr; E = MEM; if F cannot supply imm+ready in 1, need F×2 (visible) |
| BEQ | 3 | ALU + PC | **NO** (3-byte + ALU/PC) | **COND** — F×3 or F+abs latch; E = ALU/PC |
| JMP | 3 | PC | **NO** | **COND** — multi-F + E PC_LOAD |
| CALL | 3+stack | BRANCH + mem assist | **NO** | **COND** — multi-F + **E×k** stack (document k) |
| RET | 1+stack | pop + PC | **NO** | **COND** — **E×k** stack |
| HALT | 1 | stop | N/A | F+E trivial |

### Slowing SYS to “buy FE1”

Lowering f_SYS lengthens the period but **does not create a second bus**. Serialized internal steps inside one labeled tick are **not** honest FE1 on this BOM. Verdict: **slow clock ≠ FE1 Go**.

### Harvard escape (out of BOM scope)

Separate insn ROM port + data RAM port could make FE1 for some ops **Conditional** at desk — **out of scope** for this breadboard regression (would be a different machine).

## FE2 ADD detail (main win vs Gi1)

```text
Gi1:  F... + ph0 idle + ph1 idle + ph2 ALU   => exec SYS waste
FE2:  F (opcode+imm) + E (ALU)               => 2 SYS visible, both real
```

At 2 MHz, ADD macros/s desk: Gi1 exec-only 2e6/3 ≈ 0.67 M → FE2 if F+E counted: 2e6/2 = 1.0 M (fetch included fairly). See [model/](model/).

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Initial matrix |
