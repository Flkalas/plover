# Breadboard v1.0 wiring reference (Gi1)

**Normative:** [system-architecture.md](../hardware/system-architecture.md) · [cpld-system-controller.md](../hardware/cpld-system-controller.md) · [cpld-dual-routing.md](../hardware/cpld-dual-routing.md)

Single breadboard target — **v1.0 Gi1 dual CPLD (idx5)**. **CPLD-CU** = FSM + strobes; **CPLD-DP** = **R0 + `q_a`**; **MBR 574 → ALU B**; CE/mailbox = **138×2 + glue**.

---

## Block placement (logical)

```text
  ROM ──► IR ──► CPLD-CU ── strobes ──► ALU / MEM / PC
                    │ reg_we
                    └──► CPLD-DP ◄── data bus
                              └── q_a ──► ALU A
  MBR 574 ──────────────────────────────► ALU B

  A[15:0] ──► 138×2 + glue ──► /CE ──► RAM×2 + ROM
```

---

## Control path

| Source | Role |
|--------|------|
| **IR[4:0]** | idx5 FSM on **CPLD-CU** |
| **MBR 574** | Operand imm8 / abs16; **Gi1: ALU B** |
| **CPLD-CU** | Direct strobes to SoC |
| **G-IC** | **`reg_we` only** → CPLD-DP (R0 write) |
| **FLG 574** | Z → CU branch @ macro_end |

---

## 574 inventory (Gi1)

| IC | Role |
|----|------|
| PC (+161 high) | Instruction address |
| IR | Opcode → CPLD-CU `OPC[4:0]` |
| MBR | Operand / abs16 low; **ALU B source** |
| FLG | Z, C |

**3× 574** total (unchanged vs rev G).

---

## CPLD ↔ ALU

| Source | ALU / bus |
|--------|-----------|
| CPLD-DP `q_a` | ALU A |
| MBR 574 `net_mbr` | ALU B |
| CPLD-CU strobes | `cin`, `bctrl*`, `lgc*`, `s0`, `s1`, `MEM_*`, `Y_OE`, `FLG_WE`, `PC_LOAD_EN` |

**Removed:** CPLD `q_b` → ALU B (rev G).

---

## Bring-up order

M1 ALU → M2a dual CPLD (Gi1 JED + MBR→B) → M2b memory → M3a FSM → M3b fetch → M4/M5.

---

## Legacy rev G wiring

[archive/rev-g-normative-snapshot/reference/hw-bringup/breadboard-wiring.md](../../archive/rev-g-normative-snapshot/reference/hw-bringup/breadboard-wiring.md)
