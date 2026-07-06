# Gi1 FSM and microcode delta

**Parent:** [README.md](README.md)  
**Baseline idx5:** [reference/hw-bringup/M3b-fetch-execute.md](../../../reference/hw-bringup/M3b-fetch-execute.md) · [reference/hardware/microcode-spec.md](../../../reference/hardware/microcode-spec.md)

---

## 1. CU changes (desk)

| Item | rev G | Gi1 |
|------|-------|-----|
| TFR comb (`tfr_valid`, `src`) | 6 G-IC wires + opcode decode | **removed** |
| `w_sel` on G-IC | 2 bits | **omitted** — DP assumes R0 |
| ADD ph2 `w_sel` | R2 (`10`) | **R0** (`00`) — internal LUT only |
| ADD ph1 `REG_WE→R1` | **mandatory** | **deasserted** |
| CMP ph1 | imm→R1 | **no R1 write** |
| `0x10–0x1F` | TFR | **trap / NOP** (reserved) |

---

## 2. ADD idx5 rows (example)

Opcode `0x01` → base `(1<<2)=4`:

| phase | idx5 | rev G strobes | Gi1 strobes |
|-------|------|---------------|-------------|
| ph0 | 4 | `Y_OE` | idle / `Y_OE` (no MBR LE) |
| ph1 | 5 | `REG_WE`, w_sel=R1 | **—** |
| ph2 | 6 | `REG_WE`, w_sel=R2, `FLG_WE`, ALU ADD | `REG_WE`→R0, `FLG_WE`, ALU ADD |

ALU controls (`cin`, `bctrl`, `lgc`, `s0/s1`) unchanged on ph2.

---

## 3. CMP idx5 rows

Opcode `0x0D` → base 52:

| phase | Gi1 |
|-------|-----|
| ph0–1 | no `REG_WE` to GPR |
| ph2 | `FLG_WE` only; ALU CMP; B from MBR |

---

## 4. MBR hold policy

```text
  ALU_REG macro active:
    - FETCH may be 0 (normal execute)
    - Do NOT clock operand byte into MBR from bus
    - net_mbr holds imm8 captured at insn fetch (PC+1)
```

| Template | MBR role | Hold required? |
|----------|----------|----------------|
| ALU_REG ADD/CMP | **imm → ALU B** | **yes** ph0–ph2 |
| MEM_LD | address | no (reload OK) |
| MEM_ST | address | no |
| BEQ/JMP | abs16 | no (post-macro) |

**Fetch unit:** IR/MBR load at macro **start** (before ph0) — unchanged from M3b.

---

## 5. DP changes

| | rev G | Gi1 |
|---|-------|-----|
| GPR FF | R0–R2 | **R0** |
| `q_a` | R0 | R0 |
| `q_b` | R1 | **not driven** |
| Write | `reg_we` + `w_sel` + xfer | **`reg_we` → R0 only** |
| `d_in` | bus write | unchanged |

---

## 6. G-IC bundle (desk)

| Signal | Direction | Gi1 |
|--------|-----------|-----|
| `reg_we` | CU → DP | GPR write strobe (R0) |
| ~~`w_sel[1:0]`~~ | — | **removed** |
| ~~`tfr_valid`~~ | — | **removed** |
| ~~`src[1:0]`~~ | — | **removed** |

**G-IC count:** **6 → 1** wire (plus shared `CLK`).

CU exports: **1** DP control line vs 6 — frees CU pins for future use.

---

## 7. Optional: 2-phase ADD

| | 3-phase | 2-phase |
|---|---------|---------|
| ph0 | bus / display | merged or dropped |
| ph1 | idle | ALU prep |
| ph2 | execute | execute |
| Wall-clock | 750 ns macro | **500 ns** macro |

Execute **250 ns** unchanged; macro latency improves.

---

## Related

- [isa-delta.md](isa-delta.md)
- [timing-closed.md](timing-closed.md)
- [../variants/gi1_dp/system_ctrl.pld](../variants/gi1_dp/system_ctrl.pld)
