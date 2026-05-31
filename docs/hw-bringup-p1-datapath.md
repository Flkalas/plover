# Phase1 — v0.2 datapath bring-up (hwsim-validated)

CW **stub nets** + **alu_decode** + **4×574 regfile** + **unchanged alu8**.  
Electrical behavior matches `python -m hwsim run` on [`cpu_datapath_p1.yaml`](../hw/netlist/blocks/cpu_datapath_p1.yaml).

Spec: [microcode-spec-v0.2.md](microcode-spec-v0.2.md) · BOM: [BOM.md §V1/V2](../BOM.md)

---

## Netlists and tests

| Block | YAML | hwsim |
|-------|------|-------|
| ALU decode | [`alu_decode.yaml`](../hw/netlist/blocks/alu_decode.yaml) | `alu_decode_full`, `alu_decode_timing` |
| Regfile | [`regfile.yaml`](../hw/netlist/blocks/regfile.yaml) | `regfile_mux`, `regfile_cmp_mask`, `regfile_rmw_4x153_slack` |
| Integrated | [`cpu_datapath_p1.yaml`](../hw/netlist/blocks/cpu_datapath_p1.yaml) | `p1_rmw_add`, `p1_rmw_sub`, `p1_cmp_no_latch` |
| + 2 MHz clock | [`cpu_datapath_p1_clock.yaml`](../hw/netlist/blocks/cpu_datapath_p1_clock.yaml) | `p1_rmw_clock` |

Regenerate merged netlists:

```bash
python tools/gen_alu_decode_netlist.py
python tools/gen_alu8_decode_netlist.py
python tools/gen_regfile_netlist.py
python tools/gen_cpu_datapath_p1_netlist.py
python tools/gen_cpu_datapath_p1_clock_netlist.py
python tools/gen_p1_tests.py
```

---

## Stub CW nets (no Flash yet)

| Net | Role |
|-----|------|
| `net_alu_op0..3` | CW `[15:12]` — drives decode → ALU control |
| `net_src_reg0..1` | A-port 153 MUX select |
| `net_dst_reg0..1` | B-port MUX + 138 CP address (IMM override when `bus_en=11`) |
| `net_bus_en0..1` | `11` → force dst=R2 (IMM path) |
| `net_cmp_n` | Decode output; AND with CP enable (CMP → no latch) |
| `net_clk2` | 574 CP gate (manual in P1 tests; OSC+74 in `*_clock` netlist) |

Opcode / control DIP reference: [hw-bringup-b3-opcode.md](hw-bringup-b3-opcode.md) (`alu_op` column).

---

## Scope probe points (breadboard later)

1. **MUX** — `net_a*`, `net_b*` vs `net_r*_q*` while stepping `src`/`dst`.
2. **Decode** — `net_alu_op*` → `net_sub_en`, `net_cmp_n` (CMP opcode **11** → `net_cmp_n=0`).
3. **RMW** — one 2 MHz cycle: `alu_op=ADD`, src=R0, dst=R2 → `net_y*` then posedge → `net_r2_q*`.
4. **CMP** — same cycle: `net_y*` updates; **`net_r2_q*` must not change** when `net_cmp_n=0`.

Timing budget: comb **≤220 ns** + setup **8 ns** (see `regfile_rmw_4x153_slack`, `p1_rmw_sub`).

---

## Out of scope (Phase2+)

Flash CW fetch, PC 161 + LOCAL branch, 245/SRAM `bus_en`, `pack_rom.py` v0.2.

---

## Related

- [hw-bringup-b3.md](hw-bringup-b3.md) — ALU-only phases B3a–c
- [roadmap-next.md](roadmap-next.md) — Phase1 milestone
