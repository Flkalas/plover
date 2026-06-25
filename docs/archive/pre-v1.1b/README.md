# Archived — CPU control-plane drafts (internal codename **v1.1b**)

> **v1.1b** was a pre-release iteration codename. Active normative label is **v1.0** (FSM-only, idx5).

**Merged into normative (2026-06-24):**

- [microcode-spec.md](../../hardware/microcode-spec.md)
- [cpld-system-controller.md](../../hardware/cpld-system-controller.md)
- [system-architecture.md](../../hardware/system-architecture.md)

**Design rationale:** [research/design-rationale-v1.0.md](../../hardware/research/design-rationale-v1.0.md)  
**Search record:** [cpu-4axis-arch-search-report.md](../../hardware/research/cpu-4axis-arch-search-report.md)  
**Superseded prototype:** [prototype-flash-cw/](../prototype-flash-cw/README.md)

## Historical Pareto winner (pre-refinement)

`op_legacy + idx4 + dec_cpld_seq + cpld_3fixed + cw_hybrid`

Post-refinement normative v1.0 dropped hybrid Flash in favour of **FSM-only idx5**.

## Contents (reference copies)

| File | Merged into |
|------|-------------|
| [microcode-spec-v1.1b.md](microcode-spec-v1.1b.md) | `hardware/microcode-spec.md` |
| [cpld-system-controller-v1.1b.md](cpld-system-controller-v1.1b.md) | `hardware/cpld-system-controller.md` |
| [opcode-expanded-control.md](opcode-expanded-control.md) | research / archive only |
| [alu-decode-architecture-study.md](alu-decode-architecture-study.md) | research |
