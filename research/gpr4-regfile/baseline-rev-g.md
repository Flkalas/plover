# Baseline — rev G (3-GPR·TFR) — **archived**

**Status:** Superseded **2026-07** by **Gi1 v1.0** normative. Do not cite for SoC bring-up.

**Normative snapshot:** [archive/rev-g-normative-snapshot/](../../archive/rev-g-normative-snapshot/) · Index: [archive/rev-g-dual-3gpr/README.md](../../archive/rev-g-dual-3gpr/README.md)

**Historical source of truth (pre-Gi1):** snapshot copies above; live reference now describes Gi1.

---

## Topology

```text
  IR OPC[4:0] ──► CPLD-CU idx5 FSM ──► MEM_RD/WR, Y_OE, FLG_WE, PC_LOAD_EN, ALU ctrl
                    │
                    └── G-IC (6) ──► CPLD-DP GPR ──► q_a[7:0], q_b[7:0] ──► ALU A/B
  d_bus[7:0] ───────────────────────► CPLD-DP (LDA write)
```

Two **ATF1504AS-10JU44** devices: **CPLD-CU** (control) + **CPLD-DP** (datapath).

---

## GPR model (CPLD-DP)

| Register | Role (v1.0 ISA) | ALU port |
|----------|-----------------|----------|
| **R0** | Accumulator; LDA/STA/CMP target | Fixed **A** (`q_a`) |
| **R1** | ADD/CMP immediate operand latch | Fixed **B** (`q_b`) |
| **R2** | ADD result; TFR source/dest | **No** async read to ALU |

- **24 flip-flops** (3×8), clocked on `CLK` (2 MHz).
- **Write:** `reg_we` + `w_sel[1:0]` — bus (`d_in`) or TFR internal mux when `tfr_valid`.
- **Read:** `q_a` = R0, `q_b` = R1 **hardwired** in PLD (`q_a0 = r00`, …).

PLD reference (archived fit-study): `fit-study/variants/g_dual_dp/system_ctrl.pld` in [fit-study-gpr-fsm.tar.gz](../../archive/fit-study-gpr-fsm.tar.gz).

---

## G-IC bundle (CU → DP, 6 wires)

| Signal | Function |
|--------|----------|
| `reg_we` | GPR write strobe (LUT ∨ TFR) |
| `w_sel[1:0]` | Write destination (R0/R1/R2) |
| `tfr_valid` | Select internal read mux vs bus for write data |
| `src[1:0]` | TFR source register (`opc[1:0]`) |

**CLK** is parallel on pin 43 (not counted in G-IC).

---

## Pin budget (rev G)

### CPLD-DP

| Direction | Signals | Count |
|-----------|---------|------:|
| In | `d_in[7:0]`, G-IC (6), `CLK` | 15 |
| Out | `q_a[7:0]`, `q_b[7:0]` | 16 |
| **Total** | | **31** / 32 (1 spare) |

### CPLD-CU

| Direction | Signals | Count |
|-----------|---------|------:|
| In | `opc[4:0]`, `flg_z`, `CLK` | 7 |
| Out SoC | direct strobes | 14 |
| Out G-IC | 6 | 6 |
| **Total** | | **26** / 32 (6 spare) |

Desk MC: CU ~29–35, DP ~18–28. Bring-up gate: WinCUPL **Design fits** per chip.

---

## ISA constraints driving the regfile

| Instruction | Register behavior |
|-------------|-------------------|
| **LDA** | ph1: `reg_we`, `w_sel=R0` ← mem |
| **STA** | ph0: `Y_OE`; sources **R0 only** (via `q_a`) |
| **ADD** | ph1: imm → R1; ph2: result → **R2** |
| **TFR** | 1 phase; `w_sel=dst`, `src` from opcode |
| **CMP** | uses R0 vs imm in R1 path |

**Consequence:** storing ADD result (R2) requires **TFR02** then **STA** — not a memory-path limitation alone; **STA is wired to R0**.

---

## cyclesim model

- [`simulators/cyclesim/blocks/cpld/dp.py`](../../simulators/cyclesim/blocks/cpld/dp.py) — 3 regs, fixed `qa()`/`qb()`, TFR mux.
- [`simulators/cyclesim/blocks/cpld/gic.py`](../../simulators/cyclesim/blocks/cpld/gic.py) — 6-wire `GicStrobes`.

---

## What rev G does *not* provide

- No **R3** (compiler audit: R3 unused in ISA; boot docs may mention R0–R3 as software convention only).
- No **selectable ALU read** — `r_sel` does not exist.
- No **store-from-R2/R3** without TFR to R0 first.
