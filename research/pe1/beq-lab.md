# PE1 lab — measure BEQ timing slack

**Status:** Research (non-normative)  
**Related:** [clock-candidates.md](clock-candidates.md) · [timing-budget.md](timing-budget.md) · M3b observe note ([M3b-fetch-execute.md](../../reference/hw-bringup/M3b-fetch-execute.md) §3)

## Goal

Confirm **setup slack** before the PC-capture clock edge on a **taken BEQ**, at the OSC under test (2.0 / 3.6864 / 4.0 MHz).

Pass: measured slack **≥ 50 ns** (or ≥ 20% of period if you document that choice), and correct taken/not-taken behavior for minutes.

## Setup

1. Drive `CLK_SYS` from the candidate OSC (PE1: **no ÷2** unless testing 1.8432 MHz).
2. Run a tight loop that **takes BEQ** (Z=1) and optionally a twin that **falls through** (Z=0).
3. Scope probes (×10, short ground):

| Ch | Net | Why |
|----|-----|-----|
| 1 | `CLK_SYS` | trigger / timebase |
| 2 | `PC_LOAD_EN` (CPLD-CU) | branch strobe |
| 3 | `FLG_Z` (optional) | when Z became valid |
| 4 | one `PC` bit (optional) | when PC actually changes |

## Measurement

Assume PE1 samples PC on a **rising** `CLK_SYS` after EX.

1. Trigger on CH1 rising edge in the BEQ retire / PC-load window.
2. Mark when CH2 `PC_LOAD_EN` (and path through FLG) is **stable valid**.
3. Mark the **capturing** rising edge of CH1.
4. Horizontal delta = **setup slack**.

```text
slack_ns = t_capture_edge - t_PC_LOAD_stable
```

Also functional check: known Z=1 always branches; Z=0 never does.

## Pass / fail

| Result | Action |
|--------|--------|
| slack ≥ 50 ns, stable | OSC OK for PE1 desk |
| 20–50 ns, rare mis-branch | Shorten wiring; or lower f_SYS |
| PC changes after edge / metastability | **Fail** — drop clock or stretch BEQ |

## Procedure tip

1. Capture a **golden** waveform at **2.0 MHz** first.  
2. Swap only the OSC to **3.6864** (or 4.0) and compare slack shrinkage.  
3. Record scope shot + slack ns in the bring-up log.

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Initial BEQ lab procedure |
