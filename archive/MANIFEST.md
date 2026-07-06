# Archive manifest

**Frozen:** 2026-07-04  
**Active tree:** `plover-whitepaper.md` + `reference/**` only — no `docs/` folder.

Restore: `tar -xzf archive/NAME.tar.gz -C .` from repository root.

---

## Active reference (not in tarballs)

| Path | Role |
|------|------|
| [plover-whitepaper.md](../plover-whitepaper.md) | Project main document |
| [reference/](../reference/) | v1.0 specifications, bring-up, fixtures |
| [reference/project/BOM.md](../reference/project/BOM.md) | Breadboard BOM |

---

## Bundles

| File | Contents |
|------|----------|
| `hwsim.tar.gz` | Electrical timing simulator |
| `cyclesim.tar.gz` | Micro-phase structural sim |
| `plover_vm.tar.gz` | Python logic VM |
| `rust_vm.tar.gz` | Rust workspace (`crates/`, `Cargo.toml`, `.cargo/`) |
| `tools.tar.gz` | Generators, verify scripts |
| `hw.tar.gz` | Netlists, fixtures, YAML tests |
| `tests_py.tar.gz` | pytest suite |
| `host_toolchain.tar.gz` | plover_asm, plover_cc, plover_ld, forth, kern, basic, firmware |
| `verilog_sim.tar.gz` | Legacy Verilog tree |
| `research_docs.tar.gz` | `docs/hardware/research/` — Pareto, CPLD viewers |
| `docs_archive.tar.gz` | `docs/archive/` — superseded specs, gemini |
| `developer_docs.tar.gz` | `docs/developer/`, `docs/plans/` — sim guide, implementation plans |
| `fit-study-gpr-fsm.tar.gz` | **Frozen 2026-07-06** — GPR-FSM variant studies (A1/D5a/E1/F2/G), WinCUPL fit logs, desk reports |
| [tier-c-single-cpld/](tier-c-single-cpld/) | **Superseded 2026-07-06** — single ATF1504 + CW 574×2 (pre rev G) |

`build/`, `target/`, `.venv/` — local artifacts; not bundled. Delete locally.

---

## Legacy paths

| Old path | Current |
|----------|---------|
| `docs/normative/**` | `reference/**` |
| `docs/normative/project/plover-whitepaper.md` | `plover-whitepaper.md` |
| `docs/project/plover-whitepaper.md` | `plover-whitepaper.md` |
| `docs/hardware/system-architecture.md` | `reference/hardware/system-architecture.md` |
| `docs/hw-bringup/**` | `reference/hw-bringup/**` |
| `docs/developer/**` | `developer_docs.tar.gz` |
| `docs/hardware/research/**` | `research_docs.tar.gz` |
| `docs/archive/**` | `docs_archive.tar.gz` |
| `BOM.md` (root) | `reference/project/BOM.md` |
| `archive/bundles/**` | `archive/*.tar.gz` |
| `cpld_fsm/fit-study/` (full tree) | `fit-study-gpr-fsm.tar.gz` — stub [README](../cpld_fsm/fit-study/README.md) |
| `hwsim/`, `hw/`, `tools/`, … | matching code bundle above |

---

## Agent rules

For **architecture**, **bring-up**, **timing**, or **decode**:

1. Cite **`reference/**` and `plover-whitepaper.md` only** — not restored tarball content.
2. Do **not** run or quote sim/code from `archive/*.tar.gz` unless the user explicitly asks for historical comparison.
3. **Forbidden as v1.0 SoC truth:** `alu8_decode` on breadboard, Flash `$4000` CW burn, `cpu_cw_direct`, pareto MC reports.
4. Research and developer docs exist only in tarballs — exploration history, not current spec.

### Frozen FSM snapshot (M3a)

PASS — 16 FSM opcodes, **20 active idx5 rows** (+ comb TFR) — see [reference/hw-bringup/M3a-control-store.md](../reference/hw-bringup/M3a-control-store.md) §2.

---

## Pack commands (one-time)

```powershell
tar -czf archive/research_docs.tar.gz docs/hardware/research
tar -czf archive/docs_archive.tar.gz docs/archive
tar -czf archive/developer_docs.tar.gz docs/developer docs/plans
tar -czf archive/fit-study-gpr-fsm.tar.gz -C cpld_fsm fit-study
```

Code bundles: see `archive/pack-bundles.ps1`.
