# gi1_cu_callret — WinCUPL PLD spike

CU fork: Gi1 idx5 baseline + **CALL/RET** (22 active rows) + return-stack assist @ macro_end.

## Source

1. Baseline CU port list: [cpld-system-controller.md](../../../../reference/hardware/cpld-system-controller.md)
2. Prior Gi1 CU notes: [archive/gpr4-regfile-research.tar.gz](../../../../archive/gpr4-regfile-research.tar.gz) `variants/gi1_cu/README.md`
3. Architecture: [../../architecture.md](../../architecture.md)

## Required PLD changes

| Area | Change |
|------|--------|
| idx5 LUT | Add rows opcode `0x06` phase 0 → idx5 **24**; `0x07` phase 0 → idx5 **28** |
| Strobes | Same as JMP: `PC_LOAD_EN=1`, `PC_LOAD_FLG_Z=0` |
| macro_end | Stack assist FSM for CALL (push) / RET (pop) |
| PC path | Internal mux: RET selects popped word, not MBR |

## WinCUPL procedure

1. Copy or merge into `system_ctrl.pld` (CU device ATF1504AS).
2. Fit with same constraints as Gi1 DP/CU pair (2 MHz, PLCC-44).
3. Record result in `fit-report.txt` — **Design fits** line is the gate.

## Status

| Artifact | State |
|----------|-------|
| `system_ctrl.pld` | **Pending** — desk spec complete; await CU baseline `.pld` in repo |
| `fit-report.txt` | Desk placeholder — run WinCUPL after `.pld` merge |

When `system_ctrl.pld` is added, run fitter via [cpld/tools/install-wincupl.ps1](../../../../cpld/tools/install-wincupl.ps1) toolchain and replace placeholder fit report.
