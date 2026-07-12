# P12 → serial FE2 fallback (research)

**Non-normative.**

## When

Trigger if any of:

1. PROG and DATA cannot run in the same SYS without contention (isolation fail).
2. Pipe IR / PROG latch path cannot be wired on the breadboard.
3. Lab shows systematic IF∥EX collisions that stretch cannot absorb cheaply.

## What changes

| | Pipe P12 | Fallback FE2 |
|--|----------|--------------|
| Ports | PROG∥DATA | Shared A-bus |
| Schedule | IF overlap EX | **F then E** serial |
| ALU stream IPC @ 2 MHz | **~1.0** | **~0.33** |
| Idle | Forbidden | Forbidden |
| Stretch | stall/EX +1 | E +1 (FE2 sheet) |

Model mode: `fallback_fe2` → same SYS totals as FE2 ([cycle_model.py](../primitive-one-clock/model/cycle_model.py)).

## What not to do

- Do **not** claim shared-bus FE1 (1 SYS fetch+exec full ISA).
- Do **not** reintroduce Gi1 idle phases as “temporary.”
- Prefer documenting fallback as a **named CU mode**, not silent schedule drift.

## IPC impact (desk)

At `F_SYS = 2 MHz`, ALU×20 stream:

| Mode | IPC | rate |
|------|----:|-----:|
| P12 opt | 1.000 | 2.000 M/s |
| fallback FE2 | ~0.333 | ~0.667 M/s |

Exact: `python model/p12_ipc_model.py`.

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Initial |
