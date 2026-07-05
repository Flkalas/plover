# Simulators

Developer-only hardware simulators. Not cited in `reference/**`.

## cyclesim

Functional-block cycle simulator for v1.0 CPLD idx5 FSM + ALU + M3b fetch/execute.

```bash
python -m simulators.cyclesim test
python -m simulators.cyclesim run m3b_mini.hex --ram-init 0x42=0x42
python -m simulators.cyclesim export alu8
pytest simulators/cyclesim/tests
```

`export alu8` writes `simulators/cyclesim/build/alu8_func.yaml`, `alu8_func.units.yaml`, and `alu8_func.schematic.yaml` — **12 DIP** assembly (`74HC153`×8, `74HC283`×2, `74HC157`×2). Control nets and CMP flags are ports (CPLD / observe); no behavioral glue instances.

Blocks: MUX4, ADD4, MUX2, Idx5Decoder, GPR regfile, PC/IR/MBR, memory array.

Normative source: `reference/hardware/`, `reference/hw-bringup/M3a`, `M3b`.

CPLD verification (LUT layer): [cpld_fsm/hdl/README.md](../cpld_fsm/hdl/README.md).

## Strobe layers

| Layer | Signals | Verified by |
|-------|---------|-------------|
| **LUT / csim** | `reg_we_lut`, `w_sel*_lut`, … (18 signals in `ctrl_lut.inc`) | `cpld_fsm/hdl/tests/test_csim_fsm_table.py` |
| **Merged / bench / cyclesim** | `reg_we`, `w_sel0/1`, full `bctrl0..3`, package strobes | `test_merged_strobe_parity.py`, `CtrlLookup` tests |

Merge rules live in `cpld_fsm/hdl/system_ctrl.pld` (`tfr_valid`, `bctrl1=bctrl0`, …). Reference: [control-and-decode.md](../reference/hardware/control-and-decode.md) §6.

## Parity matrix (functional)

Golden: `simulators/cyclesim/data/{isa,fsm_table}.py`. Timing (2 MHz) is **bench-only** — not simulated.

| Area | fsm_table | ctrl_lut.inc | CUPL .sim | csim LUT | CtrlLookup | CpuM3b e2e | Breadboard |
|------|-----------|--------------|-----------|----------|------------|------------|------------|
| idx5 FSM (20 rows) | source | `test_gen_ctrl_lut` | `test_sim_vs_golden` | `run_csim_lut.ps1` | `test_csim_fsm_table` | macro tests | M3a §4 |
| TFR comb | — | LUT all-low | — | — | `test_tfr_parity` | `test_tfr20`, `test_tfr_all_pairs` | M2a scope |
| Merged strobes | — | LUT eval | — | — | `test_merged_strobe_parity` | — | M2a |
| ALU macro ops | ALU rows | — | — | — | — | `test_alu8`, ADD/CMP ph1 | M1 |
| Instruction fetch | — | — | — | — | — | `test_fetch_nets`, `test_fetch_ir_mbr` | M3b F1–F3 |
| BEQ / JMP branch | rows | — | — | — | `test_merged_strobe_parity` | `test_beq_*`, `test_jmp_*`, fib | M3b F5 |
| LDA / STA / CMP | rows | — | — | — | — | `test_m3b_mini`, CMP→ADD | M3b F4 |
| LDIO / STIO | rows | — | — | — | — | `test_ldio_stio_mailbox` | M2b mailbox |
| STA16 | rows | — | — | — | — | `test_sta16_abs16_store` | — |
| RESET boot | — | — | — | — | — | `test_reset_boot_vector` | M3b F0 |
| MAP_MODE / mailbox | — | — | — | — | — | `test_map_mode_*`, `test_mailbox_*` | M2b |
| 2 MHz timing | — | — | — | — | — | — | scope |

Full regression (local):

Pre-flash gate: [cpld_fsm/hdl/verify-cpld.ps1](../cpld_fsm/hdl/verify-cpld.ps1) (Windows + WinCUPL).  
Python-only: `pytest simulators/cyclesim/tests cpld_fsm/hdl/tests -q`
