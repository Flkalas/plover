# CPLD Pipe CU — v1.0 P12 (Active)

**Status:** Active normative CU specification (**v1.0 P12**)  
**Bitstream:** WinCUPL **Design fits pending** — no Active pipe CU PLD yet  
**Devices:** CPLD-CU on **ATF1504AS-10JU44** (pair with CPLD-DP; DP role unchanged)  
**Related:** [system-architecture.md](system-architecture.md) · [control-and-decode.md](control-and-decode.md) · [cpld-system-controller.md](cpld-system-controller.md) · [microcode-spec.md](microcode-spec.md) · [call-ret-cu-fit.md](call-ret-cu-fit.md)  
**Superseded CU:** Gi1 idx5 multiphase — [archive/gi1-v1.0-normative/](../../archive/gi1-v1.0-normative/)

This document is the **single Active CU truth** for v1.0 P12. It replaces Gi1 `(opcode<<2)|phase` idle-capable schedules.

---

## 1. Design rules

1. **IF∥EX** on each `CLK_SYS` when not stalled — program fetch overlaps execute.
2. **PROG∥DATA** ports — IF must not share the DATA SRAM cycle with EX without a stall.
3. **No idle phases** — every counted SYS does IF work, EX work, a documented stall/bubble, or stretch.
4. **CPLD FSM-only** — no Flash `$4000` CW; pipe/stall PLA in CPLD-CU.
5. **Datapath kept from Gi1:** ALU A ← R0 (`q_a`); ALU B ← **MBR** `net_mbr`; G-IC **`reg_we` only**.
6. **No branch prediction** — taken redirect = visible bubble.
7. **P12 discipline:** lab fail → **stretch** (+1 visible SYS); ports fail → named **FALLBACK_FE2**; stretch before raising `f_SYS`.
8. **Fit gate:** Design fits when PLD exists — do not publish fitter used-MC counts as normative.

---

## 2. Pipeline model

```text
          SYS tick
             |
    +--------v--------+
    |  IF: PC -> PROG |----> IR / operand latch
    |  (program port) |
    +--------+--------+
             | overlap
    +--------v--------+
    |  EX: ALU / MEM  |----> retire (or stall / stretch)
    |  (data port)    |
    +-----------------+
```

| Stage | Owns | Clock |
|-------|------|-------|
| **IF** | PROG address = PC (or operand offset); latch IR / imm / abs bytes | `CLK_SYS` |
| **EX** | ALU, DATA SRAM / MMIO, `PC_LOAD_EN`, CALL/RET stack assist | `CLK_SYS` |
| **ID** | Decode inside CPLD-CU (combinational or same-edge) | — |

Steady ALU stream (imm already in operand latch from prior IF shadow): **one macro retired per SYS** while IF loads the next opcode.

### Ports

| Port | Device (normative intent) | Use |
|------|---------------------------|-----|
| **PROG** | NOR Flash (insn) via dedicated enable / latch path | IF |
| **DATA** | SRAM (and mailbox window) via existing 245 path | EX loads/stores / stack |

Same physical Flash package may remain on the board; it **must not** contend with DATA on the same SYS without entering **MEM_STALL** or **FALLBACK_FE2**.

---

## 3. State machine (desk-normative)

States are CU modes. Transitions are on `CLK_SYS` unless noted.

| State | Meaning |
|-------|---------|
| **FILL** | Pipe empty after reset / squash; IF only; no retire |
| **IF_EX** | Steady overlap: IF next byte/op; EX current macro (ALU-only) |
| **OPERAND_IF** | Extra format byte on PROG; EX may be idle of DP work this tick (still counted — not “hidden idle phase,” it is IF work) |
| **MEM_STALL** | EX uses DATA; IF held |
| **BRANCH_BUBBLE** | Taken BEQ/JMP/CALL redirect; squash IF; refetch |
| **STACK_EX** | CALL/RET multi-cycle DATA EX (push/pop) |
| **STRETCH** | Lab-driven +1 SYS on a named path (visible) |
| **FALLBACK_FE2** | Serial F then E on shared bus — **named degrade**, not wishful one-tick FE1 |

```text
RESET ──► FILL ──► IF_EX
IF_EX ──operand byte needed──► OPERAND_IF ──► IF_EX
IF_EX ──MEM/MMIO EX──────────► MEM_STALL ──► IF_EX
IF_EX ──taken redirect───────► BRANCH_BUBBLE ──► FILL/IF_EX
IF_EX ──CALL/RET─────────────► STACK_EX (+ BRANCH as needed) ──► IF_EX
any pipe state ──lab fail────► STRETCH ──► prior state
ports isolation fail ────────► FALLBACK_FE2
```

**FALLBACK_FE2** is not the normal Active schedule. Prefer fixing PROG∥DATA isolation; fallback is honesty if isolation cannot hold.

---

## 4. Bubble / SYS tax (optimistic)

```text
SYS ≈ 1                 # retire slot in steady ALU stream
    + operand_extra     # imm/abs bytes not hidden in overlap
    + mem_stall         # DATA conflict (default 1 for MEM/MMIO)
    + branch_bubble     # taken redirect (default 1)
    + stack_extra       # CALL/RET multi-cycle EX
    + stretch           # after lab fail (P12)
```

| Op | Retire | +op | +mem | +br t | +stack | Typical SYS | First stretch |
|----|-------:|----:|-----:|------:|-------:|------------:|---------------|
| ADD | 1 | 1 | 0 | 0 | 0 | **2** (stream → **1**) | rarely |
| CMP | 1 | 1 | 0 | 0 | 0 | **2** (stream → **1**) | split FLG if late |
| LDA / LDIO | 1 | 1 | 1 | 0 | 0 | **3** | +1 → **4** |
| STA / STIO | 1 | 1 | 1 | 0 | 0 | **3** | +1 → **4** |
| BEQ nt | 1 | 2 | 0 | 0 | 0 | **3** | +1 → **4** |
| BEQ t | 1 | 2 | 0 | 1 | 0 | **4** | +1 → **5** |
| JMP | 1 | 2 | 0 | 1 | 0 | **4** | rarely |
| CALL | 1 | 2 | 0 | 1 | 2 | **6** | +1 → **7** |
| RET | 1 | 0 | 0 | 1 | 2 | **4** | +1 → **5** |
| STA16 | 1 | 2 | 1 | 0 | 0 | **4** | +1 → **5** |
| HALT | 1 | 0 | 0 | 0 | 0 | **1** | — |

Optimistic packing: MEM EX packs MEM_RD+REG_WE (or Y_OE+MEM_WR) in **one** EX when lab allows.

---

## 5. Per-op control intent

| Class | IF | EX |
|-------|----|----|
| ADD/CMP | Fetch opcode/imm on PROG (imm may shadow prior EX) | ALU + `Y_OE`/`REG_WE` and/or `FLG_WE`; **MBR hold** for B |
| LDA/LDIO | Operand IF as needed | `MEM_RD` (+ `reg_we`); **MEM_STALL** |
| STA/STIO/STA16 | Operand / abs IF | `Y_OE` + `MEM_WR`; **MEM_STALL** |
| BEQ | Abs16 IF | ALU toward flags; `PC_LOAD_EN` if Z; taken → **BRANCH_BUBBLE** |
| JMP | Abs16 IF | `PC_LOAD_EN`; **BRANCH_BUBBLE** |
| CALL | Abs16 IF | Stack push EX×k + `PC_LOAD_EN`; bubble |
| RET | — | Stack pop EX×k + `PC_LOAD_EN`; bubble |
| HALT | — | Halt hold |

**CALL/RET** stack assist (RP cell `$0F00`, body `$F600–$FEEF`) remains CU-owned — see [microcode-spec.md](microcode-spec.md) §2.3. Multi-cycle DATA EX maps to **STACK_EX**, not Gi1 “macro_end after idle phases.”

**PC_in:** JMP/CALL/BEQ from abs latch; RET from popped stack word (not MBR).

---

## 6. Pin / port sketch

### Clock

| Signal | Role |
|--------|------|
| `CLK_SYS` | 2.0 MHz normative desk; IF and EX edge |

### CU inputs (desk)

| Signal | Source | Role |
|--------|--------|------|
| `OPC[4:0]` / IR | IR latch | Decode |
| `FLG_Z` | FLG 574 | BEQ |
| Port / stall sense | PROG vs DATA qualify (glue or CU) | MEM_STALL / FALLBACK |

### CU outputs — SoC strobes (reuse Gi1 net names where possible)

| Signal | Function |
|--------|----------|
| `MEM_RD`, `MEM_WR` | DATA / stack / mailbox |
| `Y_OE` | Bus drive |
| `FLG_WE` | Flag latch |
| `PC_LOAD_EN` | Redirect commit |
| `cin`, `bctrl0`, `bctrl2`, `lgc0..3`, `s0`, `s1` | ALU controls |
| PROG enable / IF latch enables | Isolate program fetch |
| DATA enable qualify | MEM path |

### G-IC (unchanged)

| Signal | Function |
|--------|----------|
| `reg_we` | R0 write → CPLD-DP |

CPLD-DP pin list and R0-only datapath: [cpld-system-controller.md](cpld-system-controller.md).

---

## 7. Timing desk (`CLK_SYS` = 2.0 MHz, T = 500 ns)

Primary budget = **full period 500 ns** (IF∥EX). Half-cycle **250 ns** is stress only.

| Path | path ns | Slack @ 500 | Slack @ 250 |
|------|--------:|------------:|------------:|
| IF (Flash→IR) | 165 | **335** | 85 |
| EX ADD | 148 | **352** | 102 |
| EX MEM | 130 | 370 | 120 |
| EX mailbox (RP ≤ 80 ns assume) | 170 | **330** | **80** |
| EX BEQ + squash | 227 | **273** | **23** |

Desk limiter under stress: **BEQ**. Mailbox is not the limiter if RP response ≤ 80 ns; else stretch MMIO EX.

Preferred trial above 2 MHz after measured BEQ slack ≥ **50 ns**: **3.6864 MHz**. Prefer stretch before clock hope.

---

## 8. P12 caveats (normative discipline)

1. **No Gi1 idle return** — do not reintroduce ADD/CMP padding phases.
2. **Stretch on fail** — unstable at low SYS → +1 visible SYS; update §4 table.
3. **FALLBACK_FE2** — only if PROG∥DATA isolation fails; serial F+E; IPC drops (ALU stream ~0.33 vs ~1.0).
4. **Optimistic IPC ≡ PE1 machine** — P12 does not add a faster schedule than the pipe in §2–§4.

---

## 9. Fit / bitstream

| Item | Status |
|------|--------|
| Active **specification** | This document |
| WinCUPL pipe CU `.pld` | **Not yet** — Design fits when written |
| Legacy Gi1 idx5 bitstream / cyclesim multiphase | **Superseded golden lag** — not Active truth |

MC desk estimates are non-normative; bring-up gate = **Design fits** only.

---

## 10. Explicit non-claims

- No claim that breadboard already runs IF∥EX lab PASS.
- No Active pipe CU bitstream.
- Executable cyclesim golden may still implement Gi1 multiphase until rewritten — treat as **legacy**, not Active.

---

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | **Active v1.0 P12** pipe CU — Gi1 idx5 CU superseded |
