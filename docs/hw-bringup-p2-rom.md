# Phase2 — ROM CW supply (hwsim-validated)

Behavioral **ROM16** drives the 16-bit CW bus each cycle; Phase1 **stub CW stimulus removed** on Phase2 tests.  
PC is a **manual `net_pc*` stub** or **PC8 auto-increment** (Phase3 replaces with 74HC161).

Spec: [microcode-spec-v0.2.md](microcode-spec-v0.2.md) · Plan: [v0.2-implementation-plan.md](v0.2-implementation-plan.md)

---

## Netlists and tests

| Block | YAML | hwsim |
|-------|------|-------|
| ROM fetch | [`rom_fetch.yaml`](../hw/netlist/blocks/rom_fetch.yaml) | `rom_fetch_word`, `rom_fetch_timing` |
| + PC8 auto | [`rom_fetch_pc8.yaml`](../hw/netlist/blocks/rom_fetch_pc8.yaml) | (merged into clock netlist) |
| Integrated | [`cpu_datapath_p2.yaml`](../hw/netlist/blocks/cpu_datapath_p2.yaml) | `p2_rom_rmw_add`, `p2_imm_load` |
| + 2 MHz clock | [`cpu_datapath_p2_clock.yaml`](../hw/netlist/blocks/cpu_datapath_p2_clock.yaml) | `p2_rom_program` |

Regenerate:

```bash
python tools/pack_rom.py --build-fixtures
python tools/gen_rom_fetch_netlist.py
python tools/gen_rom_fetch_netlist.py --pc8
python tools/gen_regfile_netlist.py          # IMM B mux (2B)
python tools/gen_cpu_datapath_p2_netlist.py
python tools/gen_cpu_datapath_p2_netlist.py --clock
python tools/gen_p2_tests.py
python -m hwsim run --all
```

---

## CW from ROM (replaces Phase1 stub)

| CW bit | Net |
|--------|-----|
| 15:12 | `net_alu_op3..0` |
| 11:10 | `net_src_reg1..0` |
| 9:8 | `net_dst_reg1..0` |
| 7:6 | `net_bus_en1..0` |
| 5:0 | `net_ctrl5..0` (IMM literal low bits when `bus_en=11`; LOCAL decode in Phase3) |

**ROM16** (behavioral): `A0..7` ← `net_pc*`, `D0..15` → CW field nets, comb `t_pd` ≤40 ns.  
Test images: `rom_image:` inline or `rom_image_file:` → [`hw/fixtures/rom/`](../hw/fixtures/rom/).

---

## PC modes

| Mode | Instance | Use |
|------|----------|-----|
| Manual | stimulus sets `net_pc0..7` | `rom_fetch_word`, `p2_imm_load`, long `p2_rom_rmw_add` |
| Auto++ | `U_PC8` / `PC8_AUTO` on `net_clk2` **negedge** | `p2_rom_program` with real 2 MHz divider |

Phase3 swaps `U_PC8` for 161 chain + LOCAL branch; ref name `U_PC8` kept as merge anchor.

---

## Tools — `pack_rom.py` v0.2

```bash
python tools/pack_rom.py --build-fixtures
python tools/pack_rom.py --demo clock_add_demo
```

`pack_cw(alu_op, src, dst, bus_en, ctrl)` → 16-bit word per spec MSB-first field order.  
Fixtures: `single_add`, `clock_add_demo`, `rmw_add`, `imm_a5`.

IMM literals use **ADD src=R2** + `bus_en=11` (not PASS_B — AND path needs A=0xFF).

---

## Scope (Phase2)

| In | Out |
|----|-----|
| ROM16 + CW split, PC stub, IMM→B | PC 161 + branches |
| `pack_rom.py`, fixture hex | microasm parser |
| hwsim PASS (27 tests) | Flash programming (see B4) |
| regfile 8×157 IMM B mux | MEM 245/SRAM |

Real Flash (`SST39SF010A`) timing omitted in hwsim; part name reserved for Phase5+.

---

## Verification matrix

| Test | PC | ROM | Check |
|------|-----|-----|-------|
| `rom_fetch_word` | manual | 1 word | CW bits = `pack_rom` |
| `p2_rom_rmw_add` | manual step | 71 words | = `p1_rmw_add` R2=0x46 |
| `p2_rom_program` | auto++ | 4 words | = `p1_rmw_clock` R2=0x02 |
| `p2_imm_load` | manual | IMM CW | R2=0xA5 |
| `rom_fetch_timing` | manual | 1 word | comb slack ≥ 0 |

[`alu8.yaml`](../hw/netlist/blocks/alu8.yaml) unchanged from B3/Phase1.
