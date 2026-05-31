# B3 — ALU + 574 accumulator bring-up (phased)

Breadboard procedure in three steps: **B3a** (comb Y) → **B3b** (manual latch) → **B3c** (2 MHz clock).  
Electrical behavior is validated in hwsim before wiring.

**Opcode cheat sheet:** [hw-bringup-b3-opcode.md](hw-bringup-b3-opcode.md) — DIP settings for all 12 opcodes.

| Phase | Netlist | hwsim |
|-------|---------|-------|
| **B3a** | [`alu8.yaml`](../hw/netlist/blocks/alu8.yaml) | `alu8_full.yaml` |
| **B3b** | [`alu_b3.yaml`](../hw/netlist/blocks/alu_b3.yaml) | `alu_b3_latch.yaml` |
| **B3c** | [`alu_b3_clock.yaml`](../hw/netlist/blocks/alu_b3_clock.yaml) | `bringup_b3c_clock.yaml` |

Target clock (B3c): **2 MHz** — 500 ns period, **250 ns** comb budget before posedge.

---

## Common — power and decoupling

- **0.1 µF per IC**, **10 µF** bulk on 5 V rail.
- Control inputs: use [opcode cheat sheet](hw-bringup-b3-opcode.md); tie unused control nets to GND unless the sheet says VCC.
- **INC/DEC:** do not drive `net_b0..7`; use `net_b_const_sel` + `net_b_const_bit1..7` only (bit0 constant is VCC in netlist).

---

## B3a — ALU only, Y LED (no clock)

**Goal:** Verify 12 opcode comb logic without 574 or clock.

### Parts

| Block | IC count |
|-------|----------|
| ALU core | **20** — see [`alu8.md`](../hw/netlist/blocks/alu8.md) |

No 574, no OSC/74.

### Wiring

1. **Power** — 5 V, GND, decoupling on every DIP.
2. **ALU core** — ref order in [`alu8.yaml`](../hw/netlist/blocks/alu8.yaml): 283 → 86 → 157 (B → **B2** → OUT) → 153 → 08/32/04.
3. **Operands** — DIP ×16: `net_a0..7`, `net_b0..7` (B ignored for INC/DEC).
4. **Control** — DIP or tie per cheat sheet: `sub_en`, `cin`, `153_s0/s1`, `b_sel`, `b_const_sel`, `b_const_bit1..7`, `c3_sel`.
5. **Output** — **`net_y0..7` → LED ×8** (330 Ω–1 kΩ); optional `net_c_hi` LED.

### Procedure

1. Look up opcode row in [cheat sheet](hw-bringup-b3-opcode.md).
2. Set A, B, and control DIP/ties.
3. Read **Y LEDs** — no clock, no wait beyond comb settling (~µs on breadboard).

### Smoke (first power-on)

| Op | A | B | Expected Y |
|----|---|---|------------|
| SUB | 0x12 | 0x34 | 0xDE |
| XOR | 0x12 | 0x34 | 0x26 |
| INC | 0x12 | — | 0x13 |

### Done criteria

- [ ] 20 IC powered and decoupled
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

**No scope:** `python -m hwsim run hw/tests/bringup_b3c_clock.yaml --report` → [`hw/viewer/index.html`](../hw/viewer/index.html).

### hwsim

```bash
python -m hwsim run hw/tests/bringup_b3c_clock.yaml
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

Timing @ max corner: SUB comb ~169 ns, XOR ~61 ns (within 250 ns half-period @ 2 MHz in hwsim).

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
| Y wrong (B3a) | Re-check cheat sheet row; verify 157 B2 for INC/DEC |
| Q ≠ Y after CP | Setup violation — slow CP edge or delay pulse until Y stable |
| Q wrong @ 2 MHz | Scope Y vs clk; lower clock or shorten wires |
| hwsim FAIL | `python -m hwsim run hw/tests/bringup_b3c_clock.yaml --report` |

Regenerate netlists: `python tools/gen_alu_b3_netlist.py`, `python tools/gen_alu_b3_clock_netlist.py`.
