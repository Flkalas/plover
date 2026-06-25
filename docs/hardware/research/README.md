# Hardware research

**Normative specs:** [system-architecture.md](../system-architecture.md) · [microcode-spec.md](../microcode-spec.md) · [cpld-system-controller.md](../cpld-system-controller.md)

**Audience:** Contributors who need **why** v1.0 was chosen, how alternatives were explored, or how estimates were derived.

| Document | Role | Content |
|----------|------|---------|
| [design-rationale-v1.0.md](design-rationale-v1.0.md) | **Rationale** | v1.0 decisions: FSM-only, idx5, DIP/delay/MC trade-offs |
| [cpu-4axis-arch-search-report.md](../cpu-4axis-arch-search-report.md) | **Search record** | 4-axis Pareto methodology; internal codename **v1.1b** in exploration history |
| [cpld-ctrl-extract/](cpld-ctrl-extract/README.md) | **Control extract** | CPLD FSM → 74HC/Flash alternatives + gate unit viewers |
| [hardware-architecture-synthesis.md](../hardware-architecture-synthesis.md) | **Synthesis** | Purchases, parasitics, breadboard notes |
| [alu-decode-architecture-study.md](../../archive/pre-v1.1b/alu-decode-architecture-study.md) | Study | Removing `alu8_decode` |
| [pre-v1.1b/](../../archive/pre-v1.1b/README.md) | Draft sources | Pre-normative CPU control drafts |

## Reading order

1. **Need normative facts?** → `../system-architecture.md`
2. **Need one-page “why v1.0”?** → [design-rationale-v1.0.md](design-rationale-v1.0.md)
3. **Need search methodology / Pareto corners?** → [cpu-4axis-arch-search-report.md](../cpu-4axis-arch-search-report.md)
