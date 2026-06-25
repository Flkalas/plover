# v1.0 design rationale

**Date:** 2026-06-24  
**Status:** Research — design decisions and trade-offs (not normative)  
**Normative:** [system-architecture.md](../system-architecture.md) · [microcode-spec.md](../microcode-spec.md) · [cpld-system-controller.md](../cpld-system-controller.md)

---

## 1. Summary

| Topic | v1.0 choice |
|-------|----------------|
| **Control** | **FSM-only** in ATF1504 — no Flash control store @ `$4000` |
| **Decode index** | **idx5** — `(opcode[4:0]<<2)\|phase`, 128 logical CPLD slots |
| **ISA** | Opcode `[4:0]`; Extended `0x10–0x1F` (TFR `0x10–0x15`); `0x0C` reserved |
| **Operands** | Fetch path only — **MBR** / addr MUX; no Flash param rows |
| **ALU control** | From CPLD FSM — **no `alu8_decode`** TTL block (~9 DIP removed) |
| **Metrics** | ~**20** DIP control path; **136 ns** critical delay; **~38** CPLD MC |

---

## 2. Control plane

### 2.1 From Flash CW to CPLD FSM

v1.0 drove every micro-phase from **10-bit control words** in Flash (`$4000+`), with `alu8_decode` expanding `ALU_OP` on the breadboard.

Normative v1.0 moves **repeated phase patterns** (ADD 3-phase, LDA 2-phase, etc.) into **hardwired CPLD templates**. The SST39 ROM holds **boot and program only**.

### 2.2 Operands without Flash param

| Macro | Operand source |
|-------|----------------|
| LDA, STA, CMP, LDIO, STIO | imm8 @ PC+1 → **MBR**; effective address from MBR at execute |
| BEQ, JMP, CALL, STA16 | abs16 from fetch → MBR / operand latch |
| ADD | imm8 → R1 via internal `w_sel` |
| TFR `0x10–0x15` | none — 1-byte implied |

CPLD asserts `MEM_RD`/`MEM_WR` using **already latched** MBR — not a second Flash fetch for parameters.

### 2.3 Branch and flags

- CMP / ADD / BEQ ph0: ALU sets **Z/C** → **574 FLG**
- BEQ macro end: `PC_LOAD_EN <= FLG_Z`
- JMP macro end: `PC_LOAD_EN <= 1`

---

## 3. idx5 decode

```text
fsm_index[6:0] = (opcode[4:0] << 2) | phase[1:0]
```

| Item | Specification |
|------|---------------|
| Logical slots | **128** (7-bit key inside CPLD only) |
| CPLD input | **`OPC[4:0]`** — **IR[4]** added vs 4-bit opcode decode |
| Flash A0–A6 | **Not wired** — no burn of 128 Flash rows |
| Extended opcodes | `0x10–0x1F` — TFR `0x10–0x15`; `0x16–0x1F` reserved |

**CPLD MC:** ~**38** macrocells (GPR 3fixed + idx5 K-map + TFR templates).

---

## 4. Exploration history (idx4 → idx5)

A **4-axis Cartesian Pareto search** (opcode · decode · CPLD · CW/Flash) identified a feasible winner:

`op_legacy` + **idx4** + CPLD phase FSM + 3fixed GPR + **hybrid Flash CW** (param rows @ `$4000`).

**Post-search refinement** adopted the same DIP/delay wins but **dropped hybrid Flash**:

- **idx5** instead of idx4 — supports TFR `0x10+` without Flash index extension
- **FSM-only** — Flash `$4000` unused; operands via MBR only
- **MC +4~6** vs idx4 estimate — acceptable within ATF1504 budget

Full methodology, H1/H2 corners, and gap checklist: [cpu-4axis-arch-search-report.md](../cpu-4axis-arch-search-report.md).

---

## 5. Trade-off table

| Benefit | Cost |
|---------|------|
| **−11 DIP** vs v1.0 control path (`alu8_decode` removed) | **IR[4] → CPLD** (+1 control net) |
| **−15 ns** critical path vs decode-in-series v1.0 | CPLD MC **~38** (+4~6 vs simpler idx4 map) |
| **0 Flash CW rows** — simpler ROM programming | idx5 K-map complexity |
| Extended ISA `0x10–0x1F` in CPLD | — |
| BEQ glue simplified (`PC_LOAD_EN` in CPLD) | — |

**Unchanged from search baseline:** 138×2 CE, mailbox glue, flat 64 KiB, no MMU, no IRQ.

---

## 6. Supporting studies

| Topic | Document |
|-------|----------|
| Pareto search & axes | [cpu-4axis-arch-search-report.md](../cpu-4axis-arch-search-report.md) |
| ALU timing, purchases, parasitics | [hardware-architecture-synthesis.md](../hardware-architecture-synthesis.md) |
| Decode removal study | [alu-decode-architecture-study.md](../../archive/pre-v1.1b/alu-decode-architecture-study.md) |
| Superseded v1.0 | [prototype-flash-cw/](../../archive/prototype-flash-cw/README.md) |

---

## Change log

| Date | Note |
|------|------|
| 2026-06-24 | Initial rationale — extracted from normative docs for research tier |
