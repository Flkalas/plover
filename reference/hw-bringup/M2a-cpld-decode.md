# M2a — CPLD GPR + idx5 FSM bring-up

| Field | Value |
|-------|-------|
| **Milestone** | M2a |
| **IC** | ATF1504AS-10JU44 (PLCC-44) |
| **Goal** | WinCUPL CUPL + FIT1504 JED burn; bench verify **3×GPR**, **idx5 phase FSM**, ADD/TFR smoke |
| **Normative** | [cpld-system-controller.md](../hardware/cpld-system-controller.md) · [control-word-latch.md](../hardware/control-word-latch.md) · [M3a-control-store.md](M3a-control-store.md) §2 |

---

## 1. Why M2a after M1

| Order | Reason |
|-------|--------|
| After ALU (M1) | ALU path verified before CPLD `q_a`/`q_b` integration |
| Before M2b/M3 | JED must drive 3-phase ADD and 1-phase TFR before fetch glue |
| CE decode | **138×2 + glue** — off CPLD ([breadboard-wiring.md](breadboard-wiring.md)) |
| SoC decode | **No `alu8_decode` DIP** — ALU control from **CW latch** ([control-word-latch.md](../hardware/control-word-latch.md)) |

**Prerequisite:** [M1-alu.md](M1-alu.md) B3a complete.

---

## 2. Repository artifacts

Committed CPLD sources live under **`cpld_fsm/hdl/`**:

| Artifact | Role |
|----------|------|
| `system_ctrl.pld` | CUPL top — GPR, phase FSM, XFER mux, branch |
| `ctrl_lut.inc` | **Generated** idx5 LUT (20 active rows / 128 slots; TFR comb outside) |
| `system_ctrl_gen.pld` | Merged PLD after codegen |
| `system_ctrl.jed` | JTAG fuse file for ATF1504 |
| `system_ctrl.pin` | Pin lock after fit |
| `fit_report.txt` | MC budget and fit status |

Codegen and build procedures: see **`cpld_fsm/hdl/README.md`** (developer doc — not repeated here).

Netlist lock: `cpld_fsm/netlist/cpld_system_ctrl.yaml`.

---

## 3. Pre-burn checklist

Align with [cpld-system-controller.md](../hardware/cpld-system-controller.md) §1:

- [ ] **idx5 decode:** `OPC[4:0]` from IR[4:0] — not archived idx4 (`OPC[3:0]`)
- [ ] **Internal `w_sel`:** write target from FSM table — **not** an exported package pin
- [ ] **No PARAM latch** — operands via PC/MBR fetch only
- [ ] **No Flash `$4000` CW** — FSM-only control
- [ ] **No `alu8_decode`** on SoC breadboard
- [ ] **3 GPR:** R0→`q_a`, R1→`q_b`, R2 via internal read for XFER
- [ ] **Fitter:** WinCUPL reports **Design fits** on ATF1504AS
- [ ] **Pre-flash gate:** local Tier 0–2 verification (codegen, pytest, CUPL `.sim`, csim LUT) complete per `cpld_fsm/hdl/README.md` — before first JTAG program
- [ ] **CW latch wired:** `CW_LO`/`CW_HI` 574, `cw_le`/`cw_bank`/`cw_data` from CPLD per [control-word-latch.md](../hardware/control-word-latch.md)
- [ ] **Frozen table:** 20 idx5 slots match [M3a-control-store.md](M3a-control-store.md) §2 and committed `ctrl_lut.inc`

---

## 4. Equipment

| Item | Spec |
|------|------|
| Programmer | ATF1500 ISP (Atmel-ICE, etc.) |
| Socket | PLCC-44 → 2.54 mm DIP adapter ([BOM.md](../project/BOM.md) #15) |
| ISP header | 2×5, 1.27 mm JTAG, **≤10 cm** cable |
| Power | Breadboard CPU **5 V** |
| Bench | DIP switches, LED+1kΩ, logic probe, DSO (2 MHz) |

---

## 5. ISP wiring

| Signal | Function |
|--------|----------|
| TCK / TMS / TDI / TDO | JTAG |
| VCC / GND | Target power (5 V during burn) |

- **0.1 µF** at CPLD VCC–GND (adapter, shortest path).
- Keep ISP cable away from 2 MHz clock tree.

---

## 6. Burn procedure

1. Confirm pre-burn checklist §3.
2. Program **`system_ctrl.jed`** via JTAG ISP.
3. Read back device ID — ATF1504 family.
4. Power-cycle target; scope **CLK** (pin 43, GCLK1) if fitted.

Pin assignments after fit: **`system_ctrl.pin`** + `cpld_system_ctrl.yaml`.

---

## 7. Bench vectors (idx5 decimal keys)

Use [M3a-control-store.md](M3a-control-store.md) §2 for full slot list. Key smoke tests:

### ADD (`0x01`) — 3 phases

| phase | idx5 | Observe |
|-------|------|---------|
| 0 | 4 | `Y_OE`, ALU ADD, R0→A |
| 1 | 5 | **REG_WE**, `w_sel=R1`, imm8→R1 |
| 2 | 6 | REG_WE, `w_sel=R2`, FLG_WE |

### TFR20 (`0x18`) — 1 phase

| phase | idx5 | Observe |
|-------|------|---------|
| 0 | 96 (inactive LUT; `tfr_valid` comb) | REG_WE, `w_sel=R2`, internal XFER (R0→R2) |

Drive `OPC[4:0]` and phase manually or via integrated fetch (M3b). Probe `REG_WE`, `MEM_RD`/`MEM_WR`, `Y_OE`, `q_a`/`q_b`.

---

## 8. M2a sign-off

- [ ] JED readback OK; device ID matches ATF1504
- [ ] ADD 3-phase strobes match §7 table (scope)
- [ ] TFR20 comb smoke — R2 latch from R0 path
- [ ] MC ≤ 64 in fitter log (`fit_report.txt`)
- [ ] Cross-check [M3a-control-store.md](M3a-control-store.md) §4

---

## 9. Archive — superseded prototype paths

**Not normative for v1.0 SoC:**

| Item | Status |
|------|--------|
| idx4 decode (`OPC[3:0]`, 64 slots) | Archive — see [control-and-decode.md](../hardware/control-and-decode.md) |
| Flash `$4000` 10b CW | [prototype-flash-cw](../../archive/prototype-flash-cw/README.md) |
| VHDL / ProChip flow | Removed — WinCUPL CUPL is v1.0 path |
| `cpu_cw_direct_add.yaml` (P1 bypass) | P1 bench only — archive |
| Exported `REG_WSEL` pin | Replaced by internal `w_sel` |

Historical tooling index: [archive/MANIFEST.md](../../archive/MANIFEST.md).

---

## Change log

| Date | Note |
|------|------|
| 2026-07-06 | Full rewrite: idx5, `cpld_fsm/hdl`, WinCUPL JED; archive idx4/PARAM/VHDL |
| 2026-06-24 | v1.0 FSM-only bring-up draft |
