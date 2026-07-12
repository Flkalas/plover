# P12 programmer timing model (research)

**Non-normative.** Combines PE1 pipe visibility with FE2 stretch language.

## What the programmer counts

```text
this instruction costs N SYS clocks
```

**N** comes from the [opcode-pipe-table.md](opcode-pipe-table.md), not from hidden CU idle rows.

| Model | What you count | Hidden idle? |
|-------|----------------|--------------|
| Gi1 | Opcode-varying multiphase | **Yes** (ADD/CMP ph0–1) |
| FE2 | F + E (multi-F/E listed) | No |
| PE1 / **P12 opt** | retire + operand + stall + bubble + stack | No |
| **P12 stretch** | same + documented stretch | No |
| **fallback FE2** | FE2 F+E sheet | No |

## Stretch policy (from FE2)

1. Baseline numbers are **optimistic**.
2. Lab first at **low SYS**. If still unstable → **add visible SYS** (stretch column), update sheet and model.
3. Stretch is still programmer-visible. Prefer stretch over raising f_SYS as the first fix.

## Pipe vs serial

Normal P12 is **overlapped** IF|EX. Serial F→E is only [fallback-fe2.md](fallback-fe2.md).

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Initial |
