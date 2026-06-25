# Agent instructions (Plover)

Repository-wide guidance for coding agents. Cursor users: the same rules live in `.cursor/rules/git-workflow-safety.mdc` (local; `.cursor/` is gitignored).

---

## Git workflow safety

### Commits after work units

When a **plan, user message, or session goal** says to finish with commits (e.g. “의미 단위 커밋”, “작업 단위가 끝나면 커밋”), **commit before ending the turn** — do not leave completed work uncommitted.

Split into **separate commits** when changes belong to different concerns (e.g. UTF-8 recovery vs a new feature).

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

Only create commits when the user or an active plan requests them; when they do, follow the procedure above in the same session — do not defer to a later turn.
