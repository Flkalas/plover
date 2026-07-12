# Archive manifest

**Frozen:** 2026-07-04  
**Active tree:** `plover-whitepaper.md` + `reference/**` only — no `docs/` folder.

Restore: `tar -xzf archive/NAME.tar.gz -C .` from repository root.

---

## Active reference (not in tarballs)

| Path | Role |
|------|------|
| [plover-whitepaper.md](../plover-whitepaper.md) | Project main document (**v1.0 P12**) |
| [reference/](../reference/) | v1.0 P12 specifications, bring-up, fixtures |
| [reference/hardware/cpld-pipe-cu.md](../reference/hardware/cpld-pipe-cu.md) | **Active pipe CU** |
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
| `cpld-rev-g-hdl.tar.gz` | **Frozen 2026-07-06** — rev G dual CPLD HDL (`hdl/`, `netlist/`) — restore before WinCUPL build |
| `gpr4-regfile-research.tar.gz` | **Frozen 2026-07-07** — 4-GPR / P1 / P1M1 / Gi1 feasibility study (`research/gpr4-regfile/`) |
| `p12-era-research.tar.gz` | **Frozen 2026-07-13** — call-ret / cpld-ustep / primitive-one-clock / pe1 / p12 desk studies (fed **v1.0 P12**) |
| [p12-era-research/](p12-era-research/) | Index README for `p12-era-research.tar.gz` |
| [tier-c-single-cpld/](tier-c-single-cpld/) | **Superseded 2026-07-06** — single ATF1504 + CW 574×2 (pre rev G) |
| [rev-g-normative-snapshot/](rev-g-normative-snapshot/) | **Frozen 2026-07-07** — rev G normative prose before Gi1 adoption |
| [rev-g-dual-3gpr/](rev-g-dual-3gpr/) | **Superseded 2026-07-07** — rev G 3-GPR + TFR index |
| [gi1-v1.0-normative/](gi1-v1.0-normative/) | **Superseded 2026-07-13** — Gi1 idx5 multiphase normative before **v1.0 P12** |
| [reference-background/](reference-background/) | **Frozen 2026-07-13** — peer comparisons + FPGA guide (not Active implementer specs) |
| `pl-dos-fs-interchange-notes.tar.gz` | **Frozen 2026-07-13** — PL-DOS / SD FDD interchange design notes (not Active) |
| [pl-dos-fs-interchange-notes/](pl-dos-fs-interchange-notes/) | Index README for `pl-dos-fs-interchange-notes.tar.gz` |

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
| `research/gpr4-regfile/**` | `gpr4-regfile-research.tar.gz` |
| `research/call-ret-cu-fit/**`, `pe1/**`, `p12/**`, … | `p12-era-research.tar.gz` |
| `docs/archive/**` | `docs_archive.tar.gz` |
| `BOM.md` (root) | `reference/project/BOM.md` |
| `archive/bundles/**` | `archive/*.tar.gz` |
| `cpld_fsm/` (full tree) | `cpld/` — **tools only**; HDL in `cpld-rev-g-hdl.tar.gz` |
| `cpld_fsm/fit-study/` (full tree) | `fit-study-gpr-fsm.tar.gz` — restore to `cpld/fit-study` |
| `hwsim/`, `hw/`, `tools/`, … | matching code bundle above |

---

## Agent rules

For **architecture**, **bring-up**, **timing**, or **decode**:

1. Cite **`reference/**` and `plover-whitepaper.md` only** — not restored tarball content.
2. Do **not** run or quote sim/code from `archive/*.tar.gz` unless the user explicitly asks for historical comparison.
3. **Forbidden as v1.0 SoC truth:** `alu8_decode` on breadboard, Flash `$4000` CW burn, `cpu_cw_direct`, pareto MC reports.
4. Research and developer docs exist only in tarballs — exploration history, not current spec. **No `research/` folder in the active tree** — restore `gpr4-regfile-research.tar.gz` or `p12-era-research.tar.gz` only when comparing history.

### Frozen FSM snapshot (M3a) — Gi1 legacy

Historical Gi1 idx5 rows — see [gi1-v1.0-normative/](gi1-v1.0-normative/) bring-up copies. **Active CU:** [reference/hardware/cpld-pipe-cu.md](../reference/hardware/cpld-pipe-cu.md).

---

## Pack commands (one-time)

```powershell
tar -czf archive/research_docs.tar.gz docs/hardware/research
tar -czf archive/docs_archive.tar.gz docs/archive
tar -czf archive/developer_docs.tar.gz docs/developer docs/plans
tar -czf archive/fit-study-gpr-fsm.tar.gz -C cpld fit-study
tar -czf archive/cpld-rev-g-hdl.tar.gz -C cpld hdl netlist
tar -czf archive/gpr4-regfile-research.tar.gz research
```

Code bundles: see `archive/pack-bundles.ps1`.
