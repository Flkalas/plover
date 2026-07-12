# P12-era research studies (archived)

**Frozen:** 2026-07-13  
**Bundle:** [p12-era-research.tar.gz](../p12-era-research.tar.gz)  
**Superseded by Active:** [v1.0 P12](../../reference/hardware/system-architecture.md) · [cpld-pipe-cu.md](../../reference/hardware/cpld-pipe-cu.md)

Desk studies that fed the Active pipe CU adoption. **Not** Active normative — restore only for history.

## Contents (inside tarball as `research/…`)

| Study | Role |
|-------|------|
| `call-ret-cu-fit/` | CALL/RET CU MC/pin desk (Conditional Go) |
| `cpld-ustep/` | Related-clock CU µstep IPC (pedagogy alternative) |
| `primitive-one-clock/` | FE1 No / FE2 Conditional Go |
| `pe1/` | IF\|EX + PROG∥DATA machine (fed P12 body) |
| `p12/` | PE1 + FE2 stretch/fallback discipline (fed P12 caveats) |

## Restore

```text
tar -xzf archive/p12-era-research.tar.gz -C .
```

Restores `research/` at repository root. Delete locally when done; do not cite as Active SoC truth.

## Current normative

[plover-whitepaper.md](../../plover-whitepaper.md) · [reference/hardware/cpld-pipe-cu.md](../../reference/hardware/cpld-pipe-cu.md)
