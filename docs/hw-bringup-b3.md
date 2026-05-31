# B3 — ALU + 574 accumulator bring-up

Breadboard procedure for the integrated **alu8 + 74HC574 ACC** block. Electrical behavior is validated in hwsim before wiring.

**Netlist:** [`hw/netlist/blocks/alu_b3.yaml`](../hw/netlist/blocks/alu_b3.yaml)  
**Tests:** `python -m hwsim run hw/tests/alu_b3_*.yaml` (4 files) or `python -m hwsim run --all`

Target clock: **2 MHz** (500 ns period, **250 ns** comb budget before posedge).

---

## Parts on this sheet

| Block | IC count | Notes |
|-------|----------|-------|
| ALU core | 20 | See [`alu8.md`](../hw/netlist/blocks/alu8.md) — includes **157 B2** cascade for INC/DEC |
| 574 ACC | 1 | `U_REG_574_ACC` — D←`net_y*`, Q→`net_q*`, CP←`net_clk` |
| Clock (optional) | 2 | 74+04 from [`clock.yaml`](../hw/netlist/blocks/clock.yaml) for live 2 MHz |

Decoupling: **0.1 µF per IC**, bulk 10 µF on 5 V rail.

---

## Wiring order

1. **Power** — 5 V, GND, decoupling on every DIP.
2. **ALU core** — follow ref order in [`alu8.yaml`](../hw/netlist/blocks/alu8.yaml): 283 → 86 → 157 (B → **B2** → OUT) → 153 → 08/32/04.
3. **574 ACC** — `net_y0..7` → `D0..7`; `CP` ← `net_clk`; `OE` → GND (always enabled for bring-up); `Q*` → LEDs or probe points (`net_q*`).
4. **Clock** — tie `net_clk` to 2 MHz divider output, or leave on DIP for manual step during first smoke test.
5. **Stimulus** — DIP switches or wires for `net_a*`, control nets (`net_sub_en`, `net_153_s0/s1`, `net_b_sel`, `net_b_const_sel`, `net_b_const_bit1..7`, `net_c3_sel`, `net_cin`).

### INC/DEC (157 B2 cascade)

| Net | INC (9) | DEC (10) |
|-----|---------|----------|
| `net_b_sel` | 0 | 0 |
| `net_b_const_sel` | 1 | 1 |
| `net_b_const_bit1..7` | 0 | 1 |
| `net_sub_en` | 0 | 0 |

Bit0 constant is wired **VCC** in netlist (`0x01` / `0xFF` LSB). Do **not** drive `net_b*` directly for INC/DEC — use cascade control only.

---

## Fixed test vectors

Use the same vectors as hwsim critical tests:

| Op | A | B (register) | Control | Y (hex) |
|----|---|--------------|---------|---------|
| **SUB** | `0x12` | `0x34` | sub=1, cin=1, b_sel=1 | `0xDE` |
| **XOR** | `0x12` | `0x34` | s1:s0=11, sub=0 | `0x26` |
| **INC** | `0x12` | — | b_const_sel=1, bits1–7=0 | `0x13` |
| **DEC** | `0x12` | — | b_const_sel=1, bits1–7=1 | `0x11` |

After comb settles, pulse **574 CP ↑** to latch Y into Q; compare Q to Y.

---

## Oscilloscope checklist (2 MHz)

| Measurement | CH-A | CH-B | Trigger | Pass |
|-------------|------|------|---------|------|
| A→Y (comb) | `net_y0` or LED | `net_a0` | A edge | Y stable **&lt; 250 ns** before next clk ↑ |
| 574 setup | `net_d0` (=Y0) | `net_clk` | clk ↑ | D stable **≥ 5 ns** before clk ↑ (74HC574 max) |
| Longest path (visual) | `net_y7` | clk | clk ↑ | MSB settled with margin |

**No scope:** open [`hw/viewer/index.html`](../hw/viewer/index.html) with hwsim `waves.json` from `python -m hwsim run hw/tests/alu_b3_sub_critical.yaml --report`.

---

## hwsim ↔ breadboard map

| hwsim | Breadboard |
|-------|------------|
| Stimulus `net_a*` | DIP / future 574 Q loopback |
| `net_b_const_sel`, `net_b_const_bit*` | DIP or decode stub |
| `net_clk` 125 ns half-period | 74+04 divider @ 2 MHz |
| Slack FAIL @ max timing | Lower clock to **~1.7 MHz** or shorten longest SUB path wiring |

### Timing notes (max datasheet corner)

hwsim slack sums **output-pin** propagation only (SUB ~169 ns @ max, XOR ~76 ns). Both pass the **250 ns** half-period budget @ 2 MHz. If scope shows insufficient margin on SUB MSB, lower clock or shorten carry-chain wiring.

---

## Ref ↔ net (574)

| Ref | Pin | Net |
|-----|-----|-----|
| `U_REG_574_ACC` | D0..D7 | `net_y0..7` |
| | Q0..Q7 | `net_q0..7` |
| | CP | `net_clk` |
| | OE | GND |

Full ALU ref table: [`alu8.md`](../hw/netlist/blocks/alu8.md).

---

## Done criteria

- [ ] SUB and XOR vectors match LEDs / scope at 2 MHz (or documented lower clock)
- [ ] INC/DEC via **157 B2** only (no `net_b` stimulus)
- [ ] 574 latches Y→Q on CP ↑ with setup margin
- [ ] `python -m hwsim run --all` PASS (9 tests)
