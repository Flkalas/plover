# B3 — ALU + 574 accumulator bring-up (phased)

> **Canonical:** [hw-bringup/M1-b3-procedure.md](hw-bringup/M1-b3-procedure.md) (상세 절차) · [hw-bringup/M1-alu.md](hw-bringup/M1-alu.md) (sign-off).  
> 이 파일은 레거시 복사본 — 신규 편집은 `hw-bringup/` 쪽을 우선합니다.

Breadboard procedure in three steps: **B3a** (comb Y) → **B3b** (manual latch) → **B3c** (2 MHz clock).  
Electrical behavior is validated in hwsim before wiring.

**Opcode cheat sheet:** [hw-bringup-b3-opcode.md](hw-bringup/b3-opcode.md) — DIP settings for all 12 opcodes.

**ALU only — step-by-step assembly (14 IC, Phase B2):** [hw-bringup-alu8-assembly-spec.md](hw-bringup/alu8-assembly-spec.md) (Korean build spec).

| Phase | Netlist | hwsim |
|-------|---------|-------|
| **B3a** | [`alu8.yaml`](../hw/netlist/blocks/alu8.yaml) | `alu8_full.yaml` |
| **B3b** | [`alu_b3.yaml`](../hw/netlist/blocks/alu_b3.yaml) | `alu_b3_latch.yaml` |
| **B3c** | [`alu_b3_clock.yaml`](../hw/netlist/blocks/alu_b3_clock.yaml) | Wiring only — **scope** @ 2 MHz (no hwsim OSC) |

Target clock (B3c): **2 MHz** — 500 ns period, **250 ns** comb budget before posedge.

---

## Common — power and decoupling

- **0.1 µF per IC**, **10 µF** bulk on 5 V rail.
- Control inputs: use [opcode cheat sheet](hw-bringup/b3-opcode.md); tie unused control nets to GND unless the sheet says VCC.
- **INC/DEC:** do not drive `net_b0..7`; use `net_b_const_sel` + `net_b_const_bit1..7` only (bit0 constant is VCC in netlist).

---

## B3a — ALU only, Y LED (no clock)

**Goal:** Verify 12 opcode comb logic without 574 or clock.

### Parts

| Block | IC count |
|-------|----------|
| ALU core | **24** — see [`alu8.md`](../hw/netlist/blocks/alu8.md) |

No 574, no OSC/74.

### Wiring

1. **Power** — 5 V, GND, decoupling on every DIP.
2. **ALU core** — ref order in [`alu8.yaml`](../hw/netlist/blocks/alu8.yaml): 283 → 04 BINV → **153_B** → 283 → **153_L** (logic) → **157_YBP** (sum vs logic → Y); CMP flags from SUB (`net_y`, `net_c_hi`).
3. **Operands** — DIP ×16: `net_a0..7`, `net_b0..7` (B ignored for INC/DEC).
4. **Control** — DIP or tie per cheat sheet: `cin`, `153_s0/s1`, `b_sel`, `b_const_sel`, `b_const_bit1..7`, `net_lgc0..3` (SUB/CMP: `b_sel=1`, `cin=1`).
5. **Output** — **`net_y0..7` → LED ×8** (330 Ω–1 kΩ); optional `net_c_hi` LED.

### Procedure

1. Look up opcode row in [cheat sheet](hw-bringup/b3-opcode.md).
2. Set A, B, and control DIP/ties.
3. Read **Y LEDs** — no clock, no wait beyond comb settling (~µs on breadboard).

### Smoke (first power-on)

| Op | A | B | Expected Y |
|----|---|---|------------|
| SUB | 0x12 | 0x34 | 0xDE |
| XOR | 0x12 | 0x34 | 0x26 |
| INC | 0x12 | — | 0x13 |

### Done criteria

- [ ] 14 IC ALU powered and decoupled
- [ ] Smoke opcodes match Y LEDs
- [ ] (Optional) all 12 opcodes from cheat sheet

---

## B3b — +574 ACC, manual CP

**Goal:** One manual clock pulse latches comb **Y** into **Q**.

### Add (B3a delta)

| Block | IC count |
|-------|----------|
| 574 ACC | **+1** — `U_REG_574_ACC` |

### Wiring delta

| Connection | Notes |
|------------|-------|
| `net_y0..7` → `574 D0..7` | Comb into latch D |
| `574 OE` → GND | Always enabled |
| `574 CP` ← **push button** | 5 V → CP when pressed; 10 kΩ pulldown; 0.1 µF debounce |
| `574 Q0..7` → **Q LED ×8** | Keep Y LEDs to compare Y vs Q |

### One “cycle”

1. Set A, B, control (same as B3a).
2. Confirm **Y LEDs** stable.
3. **Press CP once** (0 → 1 → 0).
4. **Q LEDs = Y**.

### hwsim

```bash
python -m hwsim run hw/tests/alu_b3_latch.yaml
```

### Done criteria

- [ ] SUB / XOR / INC: after CP pulse, Q = Y
- [ ] Before CP, Q holds previous value

---

## B3c — +2 MHz clock, timing margin

**Goal:** Continuous 2 MHz latch; verify setup margin (scope or hwsim).

### Add (B3b delta)

| Block | IC count |
|-------|----------|
| Clock | **+2** — 4 MHz OSC + 74HC74 ([`clock.yaml`](../hw/netlist/blocks/clock.yaml)) |

Or reuse **B1** clock board; connect **`net_clk2` → `574 CP`** (remove push button).

### Wiring delta

| Item | Change |
|------|--------|
| CP | Button removed → **`net_clk2`** (2 MHz) |
| OSC | 4 MHz → 74HC74 ÷2 → `net_clk2` |

### Oscilloscope (2 MHz)

| Measurement | CH-A | CH-B | Pass |
|-------------|------|------|------|
| Comb settling | `net_y0` | `net_clk2` | Y stable before clk ↑ |
| 574 setup | `net_d0` | `net_clk2` | D stable ≥ 5 ns before ↑ |
| MSB margin | `net_y7` | clk | SUB vector, MSB settled |

**B3c timing:** oscilloscope on real hardware — **not hwsim** (recurring OSC disabled). Pre-B3c comb margin: [`alu_b3_latch`](../hw/tests/alu_b3_latch.yaml) + [`alu_b3_sub_critical`](../hw/tests/alu_b3_sub_critical.yaml). Micro-phases / CW: `plover_vm` + [`microcode-spec.md`](microcode-spec.md).

### hwsim (comb only — no clock)

```bash
python -m hwsim run hw/tests/alu_b3_latch.yaml
python -m hwsim run --all
```

### Done criteria

- [ ] SUB vector: Q latched correctly over **≥2 clock cycles**
- [ ] Setup margin OK at 2 MHz, or documented lower clock (~1.7 MHz)

---

## hwsim ↔ breadboard

| hwsim | Breadboard |
|-------|------------|
| Stimulus `net_a*` | DIP (later: 574 Q loopback) |
| Control nets | DIP / cheat sheet ties |
| `net_clk2` @ 2 MHz | OSC + 74HC74 |
| Slack FAIL | Lower clock or shorten SUB carry wiring |

Timing @ max corner: SUB **151 ns**, logic **46 ns**, ADD **108 ns** (2 MHz Execute half-period **250 ns**). See [alu-opcodes-timing.md](alu-opcodes-timing.md) v1.3.

---

## 574 ref (B3b/B3c)

| Ref | Pin | Net |
|-----|-----|-----|
| `U_REG_574_ACC` | D0..D7 | `net_y0..7` |
| | Q0..Q7 | `net_q0..7` |
| | CP | `net_clk` (B3b) / `net_clk2` (B3c) |
| | OE | GND |

Full ALU refs: [`alu8.md`](../hw/netlist/blocks/alu8.md).

---

## Troubleshooting

| Symptom | Action |
|---------|--------|
| Y wrong (B3a) | Re-check cheat sheet; INC/DEC via **153_B** (`b_const_sel`); arith uses **157_YBP** |
| Q ≠ Y after CP | Setup violation — slow CP edge or delay pulse until Y stable |
| Q wrong @ 2 MHz | Scope Y vs clk; lower clock or shorten wires |
| hwsim FAIL | `python -m hwsim run hw/tests/alu_b3_latch.yaml --report`; B3c → scope |

Regenerate (after `alu8` change): `gen_alu_decode_netlist.py` → `gen_alu8_netlist.py` → `gen_alu_b3_netlist.py` → `gen_alu_b3_clock_netlist.py` → `gen_alu8_full_test.py` → `gen_alu8_opcode_timing.py` → `gen_opcode_cheatsheet.py` — full order in [hw-sim.md](../../simulation/hw-sim.md).
