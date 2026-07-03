# cyclesim — micro-phase structural simulator

**Python 3.10+ stdlib only.** Sits between [plover_vm](../plover_vm/) (functional ISA) and [hwsim](../hwsim/) (ns `t_pd` timing).

## Truth hierarchy

1. **[hwsim](../hwsim/)** — netlist + datasheet delays (authoritative gate behavior).
2. **cyclesim** — same netlist, [`hw/logic/`](../hw/logic/) comb/seq @ zero delay, one tick = one micro phase.
3. **[plover_vm](../plover_vm/)** — must match cyclesim for CW, Reg_Sel, GPR latch, and ALU results on normative opcodes (`0x01`–`0x0A`, `0x0D` CMP).

Reg_Sel: [`hw/micro/reg_sel.py`](../hw/micro/reg_sel.py). Parity: `pytest tests/test_cyclesim_parity.py tests/test_alu_netlist_parity.py`.

## Role

| Tool | Time axis | ALU internals |
|------|-----------|---------------|
| plover_vm | micro phase | `alu8()` black box |
| **cyclesim** | **micro phase** | **YAML netlist chips (zero-delay comb)** |
| hwsim | nanoseconds | Same netlist + datasheet delays |

**v1.0 SoC path:** [`datapath_p1.yaml`](../../hw/netlist/blocks/datapath_p1.yaml) — CPLD FSM drives `net_bctrl*`/`cin` (no `alu8_decode`).  
**M1 / isolated decode tests:** [`alu8_decode.yaml`](../../hw/netlist/blocks/alu8_decode.yaml).

One **tick** = one micro phase: apply CW / stimulus → combinational fixpoint → optional **574 CP ↑** when `REG_WE` and `LOAD_R*`.

## Commands

```bash
python -m cyclesim validate hw/netlist/blocks/datapath_p1.yaml
python -m cyclesim run --all
python -m cyclesim run hw/tests/cyclesim/datapath_add_imm.yaml
```

Artifacts: `build/cyclesim/<test>/waves.json` (probe values keyed by **phase** index).

## Test YAML

```yaml
netlist: ../../netlist/blocks/alu8_decode.yaml
driver: stimulus   # or micro
stimulus:
  - at_phase: 0
    set:
      net_alu_op0: 1
expect:
  - at_phase: 0
    net_y0: 1
```

Micro driver:

```yaml
driver: micro
opcode: 0x01
operand: 0x34
phases: 3
init:
  gpr:
    0: 0x12
    1: 0x34
expect:
  - at_phase: 2
    gpr:
      2: 0x46
```

## Netlists

| Block | Generator |
|-------|-----------|
| `datapath_p1.yaml` | `python tools/gen_datapath_p1_netlist.py` |
| `alu8_decode.yaml` | `python tools/gen_alu8_netlist.py` (existing) |

## Regeneration

```bash
python tools/gen_datapath_p1_netlist.py
python tools/gen_cyclesim_decode_test.py
python -m cyclesim run --all
pytest tests/test_cyclesim_parity.py -q
```

See also [hw-sim.md](hw-sim.md).
