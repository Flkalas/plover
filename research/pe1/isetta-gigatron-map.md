# PE1 vs Isetta / Gigatron (research map)

**Sources:** [cu-dp-comparison.md](../../reference/hardware/cu-dp-comparison.md) · [clock-comparison.md](../../reference/hardware/clock-comparison.md)

## Take

| From | What PE1 borrows |
|------|------------------|
| **Isetta** | **Simple pipeline mindset**; **no branch prediction**; control fetch overlapped with work; accept bubbles on redirect |
| **Gigatron** | **Native ~1 insn / clock** as the throughput *shape* (Harvard-ish split ROM/RAM) |
| **Both** | Extra silicon for clean ports beats pretending shared-bus FE1 works |

## Reject

| Peer feature | Why not in PE1 |
|--------------|----------------|
| Isetta **3× 24-bit Flash µcode** + 6502/Z80 emu | PE1 keeps **native** Plover macros + CPLD CU |
| Isetta **12.5 MHz µstep** as the success metric | PE1 success = **macros retired / SYS**, not µstep MHz |
| Gigatron **video/soft CPU tax** | Out of scope |
| Gigatron **pure comb CU** only | PE1 still needs a small **pipe/stall FSM** in CPLD-CU |

## Clarification (common mix-up)

Isetta’s board MHz is largely a **µstep** clock with **pipelined µword fetch**.  
PE1 does **not** aim to be an Isetta clone; it aims for **Plover-native IPC≈1** using the same *class* of idea: **overlap fetch with execute, keep control simple**.

```text
Isetta:   pipe µcode Flash  -> emulate guest ISA
Gigatron: 1 native insn/clk -> Harvard TTL
PE1:      pipe IF|EX        -> native Plover macros + BOM delta
```

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Initial |
