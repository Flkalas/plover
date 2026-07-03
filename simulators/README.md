# Simulators

Developer-only hardware simulators. Not cited in `reference/**`.

## cyclesim

Functional-block cycle simulator for v1.0 CPLD idx5 FSM + ALU + M3b fetch/execute.

```bash
python -m simulators.cyclesim test
python -m simulators.cyclesim run m3b_mini.hex --ram-init 0x42=0x42
python -m simulators.cyclesim export alu8
python -m simulators.cyclesim export alu8 --html
pytest simulators/cyclesim/tests
```

`export alu8` writes `simulators/cyclesim/build/alu8_func.yaml` and `alu8_func.units.yaml` — **12 DIP** assembly (`74HC153`×8, `74HC283`×2, `74HC157`×2). Control nets and CMP flags are ports (CPLD / observe); no behavioral glue instances.

`export alu8 --html` also writes `viewers/cyclesim-block/alu8_func/index.html` — KiCad-style 12-DIP schematic ([viewers/README.md](../viewers/README.md)).

Blocks: MUX4, ADD4, MUX2, Idx5Decoder, GPR regfile, PC/IR/MBR, memory array.

Normative source: `reference/hardware/`, `reference/hw-bringup/M3a`, `M3b`.
