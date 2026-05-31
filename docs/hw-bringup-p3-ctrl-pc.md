# Phase3 — LOCAL ctrl, flags, PC/branch (hwsim-validated)

Phase2 ROM CW supply 위에 **LOCAL `ctrl` decode**, **Z/C latch**, **16-bit PC (4×74HC161)**, **BEQ/BNE/JMP** 를 통합한다.  
MEM (`bus_en=01/10`)·microasm·IRQ mask 실장은 Phase4+.

Spec: [microcode-spec-v0.2.md](microcode-spec-v0.2.md) · Plan: [v0.2-implementation-plan.md](v0.2-implementation-plan.md)

---

## Netlists and tests

| Block | YAML | hwsim |
|-------|------|-------|
| LOCAL decode | [`local_ctrl.yaml`](../hw/netlist/blocks/local_ctrl.yaml) | `local_ctrl_decode`, `local_ctrl_priority` |
| Flag latch | [`flg_latch.yaml`](../hw/netlist/blocks/flg_latch.yaml) | `flg_we_cmp`, `flg_we_sub` |
| PC 161×4 | [`pc.yaml`](../hw/netlist/blocks/pc.yaml) | `pc_inc`, `pc_hold`, `pc_jump`, `pc_branch_*` |
| PC + decode | [`pc_local.yaml`](../hw/netlist/blocks/pc_local.yaml) | (merged for isolated PC tests) |
| Integrated | [`cpu_datapath_p3.yaml`](../hw/netlist/blocks/cpu_datapath_p3.yaml) | `cmp_flg_we`, `p3_branch_slot`, `p3_pc_sequential` |
| + ROM (no OSC) | above | manual `net_clk2` stepping (500 ns) |
| + 2 MHz clock | [`cpu_datapath_p3_clock.yaml`](../hw/netlist/blocks/cpu_datapath_p3_clock.yaml) | (reserved; OSC first-edge skew — prefer manual clk in tests) |

Regenerate:

```bash
python tools/gen_local_ctrl_netlist.py
python tools/gen_flg_latch_netlist.py
python tools/gen_pc_netlist.py
python tools/gen_regfile_netlist.py --halt-mask -o hw/netlist/blocks/regfile_halt.yaml
python tools/gen_regfile_netlist.py
python tools/gen_rom_fetch_netlist.py
python tools/gen_cpu_datapath_p3_netlist.py
python tools/gen_cpu_datapath_p3_netlist.py --clock
python tools/pack_rom.py --build-fixtures
python tools/gen_p3_tests.py
python -m hwsim run --all
```

---

## LOCAL `ctrl` (`bus_en=00`)

| Bit | Name | Phase3 |
|-----|------|--------|
| 5:4 | Branch | 00 Normal / 01 BEQ / 10 JMP / 11 BNE |
| 3 | FLG_WE | Z/C latch enable |
| 2 | INC | Normal only: 1→PC+1, 0→HOLD |
| 1 | HALT | PC·reg CP freeze (`regfile_halt`) |
| 0 | IRQ mask | stub (tie-off) |

**Priority:** HALT > JMP > BEQ/BNE > Normal  
**`bus_en≠00`:** LOCAL decode inactive (IMM/MEM `ctrl` fields do not drive PC/FLG).

Generator: [`tools/gen_local_ctrl_netlist.py`](../tools/gen_local_ctrl_netlist.py) — 74HC04/08/32 tree.

Outputs: `net_local_en`, `net_flg_we`, `net_pc_load`, `net_pc_count_en`, `net_pc_hold`, `net_halt`.

---

## Flags (Z/C, Z_prev)

| Net | Role |
|-----|------|
| `net_z_flg`, `net_c_flg` | Latched on posedge `net_clk2` when `net_flg_we=1` |
| `net_z_prev` | Previous latched Z — **branch evaluate uses this, not same-cycle FLG_WE** |

Behavioral **FLG_LATCH** reads `net_y7..0` (zero detect) and `net_c_hi` (carry).  
CMP still asserts `net_cmp_n=0` → Dst CP masked (V2).

---

## PC — 4×74HC161 (16-bit)

| Chip | Q → | P ← |
|------|-----|-----|
| U_PC_0 | `net_pc3..0` | R0[3:0] |
| U_PC_1 | `net_pc7..4` | R0[7:4] |
| U_PC_2 | `net_pc11..8` | R1[3:0] |
| U_PC_3 | `net_pc15..12` | R1[7:4] |

- **ROM fetch:** `A0..7` ← `net_pc7..0` only (Phase5까지 ROM 8-bit address).
- **Count:** ripple CET/CEP ← `net_pc_count_en` (not-taken BEQ/BNE auto PC+1).
- **Load:** `net_pc_load=1` → all `PE=1`, parallel load from `{R1,R0}`.
- **HOLD:** HALT or Normal HOLD → CEP/CET gated off.

Phase2 **PC8_AUTO** removed from `cpu_datapath_p3*`.

---

## `pack_rom.py` LOCAL helpers

```python
pack_local_ctrl(flg_we=..., inc=..., branch="beq"|"jmp"|"bne"|"normal", halt=...)
cw_cmp_flg(src, dst)   # CMP + FLG_WE + INC
cw_beq() / cw_bne() / cw_jmp() / cw_local_nop()
```

Fixtures: [`hw/fixtures/rom/branch_slot/`](../hw/fixtures/rom/branch_slot/) — INC preset → CMP+FLG → DEC R1 → BEQ → PC=3.  
[`p3_clock_add/`](../hw/fixtures/rom/p3_clock_add/) — INC R2 ×2 + ADD (R2=2).

**Note:** `cw_inc` / `cw_add` now embed `pack_local_ctrl(inc=True)` so 161 PC advances on LOCAL ALU cycles.

---

## Scope / known limits (Phase3)

| Item | Status |
|------|--------|
| MEM + branch same CW | Phase4 negative test |
| IRQ mask (ctrl0) | stub |
| Integrated OSC + 161 first posedge | use manual clk in ROM tests (see `p3_pc_sequential`) |
| `alu8.yaml` | unchanged |

---

## Gate

`python -m hwsim run --all` → **40 PASS** (27 Phase0–2 + 13 Phase3).
