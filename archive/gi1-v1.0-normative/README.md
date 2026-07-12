# Gi1 v1.0 normative (superseded)

**Superseded:** 2026-07-13 by **v1.0 P12** (IF|EX pipe CU + PROG∥DATA; PE1 machine + P12 discipline)  
**Prior normative:** Gi1 dual-CPLD, idx5 multiphase FSM, shared-bus fetch/execute, ADD/CMP idle phases

## Why P12 replaced Gi1

| Gate | Gi1 v1.0 | v1.0 P12 |
|------|----------|----------|
| CU schedule | idx5 multiphase (idle on ADD/CMP) | IF\|EX pipe; **no idle** |
| Bus | Shared von Neumann A-bus | Harvard-like **PROG∥DATA** |
| Steady ALU IPC @ 2 MHz | ~0.2 | **~1.0** (optimistic stream) |
| Datapath kept | R0 + MBR→B, G-IC `reg_we` | **Same** |

## Restore prior normative prose

| Bundle | Path |
|--------|------|
| **Normative snapshot** | [gi1-v1.0-normative/](.) (this tree) |
| Prior rev G | [rev-g-dual-3gpr/](../rev-g-dual-3gpr/) |

Snapshot includes: `plover-whitepaper.md`, `system-architecture`, `microcode-spec`, `control-and-decode`, `cpld-system-controller`, dual routing/timing, M2a/M2b/M3a/M3b bring-up excerpts as of Gi1 Active.

## Current normative

[plover-whitepaper.md](../../plover-whitepaper.md) · [reference/hardware/system-architecture.md](../../reference/hardware/system-architecture.md) · [reference/hardware/cpld-pipe-cu.md](../../reference/hardware/cpld-pipe-cu.md)
