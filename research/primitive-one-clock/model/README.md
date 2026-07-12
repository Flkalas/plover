# Cycle model (research)

**stdlib only** — `cycle_model.py`.

## Run

```text
python cycle_model.py
python -m pytest test_cycle_model.py -q
```

## Modes

| Mode | Meaning |
|------|---------|
| **gi1** | fetch bytes (1 SYS/byte) + Gi1 exec phases (incl. ADD idle) |
| **fe1** | wishful 1 SYS/insn — **non-physical** on shared bus (`fe1_possible=False`) |
| **fe2** | optimistic F+E ([opcode-fe-table.md](../opcode-fe-table.md)); stretch E if lab fails at low clock |

See parent [SUMMARY-REPORT.md](../SUMMARY-REPORT.md).
