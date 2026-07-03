# Archived code guide

**Audience:** contributors and coding agents.

The **active repository is Markdown-only** for v1.0 breadboard truth. All simulators, netlists, host toolchains, and tests live in [`archive/bundles/`](../../archive/bundles/).

---

## 1. Breadboard v1.0 truth

| Topic | Normative source |
|-------|------------------|
| Decode / ALU control | [control-and-decode.md](../normative/hardware/control-and-decode.md) |
| System blocks | [system-architecture.md](../normative/hardware/system-architecture.md) |
| FSM opcode table | [M3a-control-store.md](../normative/hw-bringup/M3a-control-store.md) §2 |
| Burn images | [fixtures/README.md](../normative/fixtures/README.md) |
| Bring-up checklist | [verification-gates.md](verification-gates.md) |

**v1.0 facts:**

- CPLD **idx5 phase FSM** drives `cin`, `net_bctrl0..3`, `lgc0..3` into **12-DIP `alu8`**.
- Flash **`$4000` control-word region is unused** — boot/program only at `$0000+`.
- There is **no `alu8_decode` block on the breadboard SoC**.

---

## 2. Terminology (do not mix)

| Breadboard v1.0 (normative) | Archived code only — **not** SoC truth |
|-------------------------------|----------------------------------------|
| CPLD FSM `bctrl*` / `cin` | `alu8_decode` 12-opcode comb bench |
| Flash `$0000+` program ROM | Flash `$4000` per-phase CW tables |
| M1 manual DIP / b3-opcode | `datapath_p1` + decode merge prototypes |
| Frozen FSM table (M3a §2) | pareto / `cpu_cw_direct` search reports |
| 12 DIP ALU BOM | 14-IC / `inc_en` legacy netlists |

---

## 3. Bundle index

See [`archive/bundles/MANIFEST.md`](../../archive/bundles/MANIFEST.md).

| Bundle | Contents |
|--------|----------|
| `hwsim.tar.gz` | Electrical timing simulator |
| `cyclesim.tar.gz` | Zero-delay micro-phase structural sim |
| `plover_vm.tar.gz` | Python logic VM |
| `rust_vm.tar.gz` | Rust workspace (`crates/`, `Cargo.toml`) |
| `tools.tar.gz` | Generators, `verify_control_store`, pareto |
| `hw.tar.gz` | Netlists, YAML tests, fixtures, logic |
| `tests_py.tar.gz` | pytest suite |
| `host_toolchain.tar.gz` | `plover_asm`, `plover_cc`, `plover_ld`, `forth`, `kern`, `basic`, `firmware` |
| `verilog_sim.tar.gz` | Legacy Verilog tree (excludes `node_modules`) |

### Restore (optional smoke)

```bash
# from repository root, after clone
tar -xzf archive/bundles/hwsim.tar.gz -C .
tar -xzf archive/bundles/tools.tar.gz -C .
# repeat per bundle; use a throwaway worktree for experiments
```

`build/` was gitignored sim output — **not** bundled; discard or regenerate only inside a restored tree.

Packing script (one-time): [`archive/bundles/pack-bundles.ps1`](../../archive/bundles/pack-bundles.ps1).

---

## 4. Agent rules

When answering **architecture**, **bring-up**, **timing fit**, or **decode** questions:

1. **Cite `docs/normative/**` only** — never `archive/bundles/**` as evidence.
2. **Do not run** or quote restored sim output unless the user explicitly asks for historical comparison.
3. **Forbidden as v1.0 gates:** `alu8_decode` on SoC, Flash `$4000` CW burn, `cpu_cw_direct`, pareto MC reports.
4. **Research / archive docs** (`docs/hardware/research/**`, `docs/archive/**`) are exploration history — not current spec.

---

## 5. Frozen FSM verification snapshot

Replaces archived `verify_control_store.py --v1.0` for active-repo work.

**Result:** PASS — 16 FSM opcodes, **26** idx5 slots — frozen **2026-07-04**.

| Opcode | Template | Phase | idx5 |
|--------|----------|-------|------|
| 0x01 | ALU_REG | 0 | 4 |
| 0x01 | ALU_REG | 1 | 5 |
| 0x01 | ALU_REG | 2 | 6 |
| 0x02 | MEM_LD | 0 | 8 |
| 0x02 | MEM_LD | 1 | 9 |
| 0x03 | MEM_ST | 0 | 12 |
| 0x03 | MEM_ST | 1 | 13 |
| 0x04 | BEQ | 0 | 16 |
| 0x04 | BEQ | 1 | 17 |
| 0x05 | JMP | 0 | 20 |
| 0x08 | MEM_LD | 0 | 32 |
| 0x08 | MEM_LD | 1 | 33 |
| 0x09 | MEM_ST | 0 | 36 |
| 0x09 | MEM_ST | 1 | 37 |
| 0x0A | HALT | 0 | 40 |
| 0x0D | ALU_REG | 0 | 52 |
| 0x0D | ALU_REG | 1 | 53 |
| 0x0D | ALU_REG | 2 | 54 |
| 0x0F | MEM_ST | 0 | 60 |
| 0x0F | MEM_ST | 1 | 61 |
| 0x10 | XFER | 0 | 64 |
| 0x11 | XFER | 0 | 68 |
| 0x12 | XFER | 0 | 72 |
| 0x13 | XFER | 0 | 76 |
| 0x14 | XFER | 0 | 80 |
| 0x15 | XFER | 0 | 84 |

Opcode summary: `0x01` ADD · `0x02` LDA · `0x03` STA · `0x04` BEQ · `0x05` JMP · `0x08` LDIO · `0x09` STIO · `0x0A` HALT · `0x0D` CMP · `0x0F` STA16 · `0x10–0x15` TFR.

Full normative copy: [M3a-control-store.md](../normative/hw-bringup/M3a-control-store.md) §2.
