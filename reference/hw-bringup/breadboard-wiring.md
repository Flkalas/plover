# Breadboard v1.0 wiring reference (rev G)

**Normative:** [system-architecture.md](../hardware/system-architecture.md) · [cpld-system-controller.md](../hardware/cpld-system-controller.md) · [cpld-dual-routing.md](../hardware/cpld-dual-routing.md)

Single breadboard target — **v1.0 rev G dual CPLD (idx5)**. **CPLD-CU** = FSM + strobes; **CPLD-DP** = GPR + full `q`; CE/mailbox = **138×2 + glue**; **no Flash CW @ `$4000`**.

---

## Block placement (logical)

```text
  ROM ──► IR ──► CPLD-CU ── strobes ──► ALU / MEM / PC
                    │ G-IC (6)
                    └──► CPLD-DP ◄── data bus
                              └── q_a/q_b ──► ALU

  A[15:0] ──► 138×2 + glue ──► /CE ──► RAM×2 + ROM
```

---

## Control path

| Source | Role |
|--------|------|
| **IR[4:0]** | idx5 FSM on **CPLD-CU** |
| **MBR 574** | Operand imm8 / abs16 |
| **CPLD-CU** | Direct strobes to SoC (no CW latch) |
| **G-IC** | `reg_we`, `w_sel`, `tfr_valid`, `src[1:0]` → **CPLD-DP** |
| **FLG 574** | Z → CU branch @ macro_end |

---

## 574 inventory (rev G)

| IC | Role |
|----|------|
| PC (+161 high) | Instruction address |
| IR | Opcode → CPLD-CU `OPC[4:0]` |
| MBR | Operand / abs16 low |
| FLG | Z, C |

**3× 574** total (CW_LO/CW_HI removed vs Tier C).

---

## CPLD ↔ ALU

| Source | ALU / bus |
|--------|-----------|
| CPLD-DP `q_a`, `q_b` | A, B (full 8b) |
| CPLD-CU strobes | `cin`, `bctrl*`, `lgc*`, `s0`, `s1`, `MEM_*`, `Y_OE`, `FLG_WE`, `PC_LOAD_EN` |

---

## Bring-up order

M1 ALU → M2a dual CPLD → M2b memory → M3a FSM → M3b fetch → M4/M5.

---

## Change log

| Date | Note |
|------|------|
| 2026-07-06 | **rev G** — dual CPLD; 574×3; CW latch archived |
