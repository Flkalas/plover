# Agent instructions (Plover)

Repository-wide guidance for coding agents. Cursor users: the same rules live in `.cursor/rules/git-workflow-safety.mdc` (local; `.cursor/` is gitignored).

---

## Git workflow safety

### Commits after work units

When a **plan, user message, or session goal** says to finish with commits (e.g. “의미 단위 커밋”, “작업 단위가 끝나면 커밋”), **commit before ending the turn** — do not leave completed work uncommitted.

Split into **separate commits** when changes belong to different concerns (e.g. UTF-8 recovery vs a new feature).

### Plan execution (auto-commit)

When **implementing an attached Cursor plan** (`.plan.md` with todos — e.g. “Implement the plan as specified”):

- **Commit without a separate “커밋하세요” request** — plan execution is sufficient permission.
- Finish with commits **before ending the turn** when plan todos are done (or at each logical unit if the plan lists “권장 커밋 단위”).
- Follow the plan’s suggested commit splits when present; otherwise split by concern (netlist/sim, decode/tests, units, docs).
- Exclude unrelated dirty files (e.g. fixtures touched by another task) unless the plan covers them.

For work **outside** an active plan, only commit when the user asks or the session goal explicitly requires it.

### Never run without explicit user request

- `git checkout -- .` or `git restore .` on tracked files (especially Korean markdown)
- `git reset --hard`
- Bulk encoding replace on `docs/**/*.md`

### Commit procedure

1. `git status` and `git diff` — confirm scope
2. Stage only files for **one** logical unit
3. Commit with a clear message (why, not a file list)
4. Repeat until the working tree is clean for finished work
5. Run relevant tests before feature commits when applicable

### When unsure

If the user asked for commits in the **same thread or plan**, treat that as permission for those commits. If scope is mixed, **split commits** rather than skipping.

When implementing a **Cursor plan**, commit in-session per **Plan execution (auto-commit)** above — do not defer to a later turn or wait for an extra commit message from the user.

---

## Document tiers (normative truth)

When answering **hardware architecture**, **bring-up**, or **decode/CPLD/ALU** questions:

| Tier | Path | Use |
|------|------|-----|
| **Normative** | `docs/normative/**` | **Single source of truth** — cite and edit here |
| **Developer** | `docs/developer/**` | Sim, CI, generators (not for external learners) |
| **Research** | `docs/hardware/research/**` | Exploration only — **do not** treat as current spec |
| **Archive** | `docs/archive/**` | Superseded — **do not** cite unless user asks for history |

**Anchor docs:** [control-and-decode.md](docs/normative/hardware/control-and-decode.md), [system-architecture.md](docs/normative/hardware/system-architecture.md).

**Active hardware truth:** `docs/normative/**` only. Archived sim/code: [archived-code-guide.md](docs/developer/archived-code-guide.md) (`archive/bundles/*.tar.gz`).

**Forbidden for SoC / bring-up answers** (unless user asks for history):

- Citing or executing restored code from `archive/bundles/**`
- `docs/hardware/research/**`, `docs/archive/**` as current spec
- Treating **`alu8_decode`** as the breadboard decode path
- Flash **`$4000`** control-word burn, **`cpu_cw_direct`**, pareto MC as v1.0 gates

**No feasibility from archived sim** — timing and fit use normative frozen numbers ([alu-opcodes-timing.md](docs/normative/hardware/alu-opcodes-timing.md)) and M2a lab checklist only.

**Do not** implement bring-up or normative edits based on archive/research content unless the user explicitly requests historical comparison.

**Stale normative terms** (after 2026-07 ALU refactor): `inc_en`, `INC_B_SEL`, `INC_2C2`, `14 IC` for ALU BOM, `b_sel`/`b_const_sel` as SoC signal names (use `net_bctrl0..3`).
