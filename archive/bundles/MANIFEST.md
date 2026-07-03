# Archive bundles

**Frozen:** 2026-07-04
**Git commit:** 31202ad

Active repository is Markdown-only for breadboard truth.
Restore: tar -xzf archive/bundles/NAME.tar.gz -C .

See docs/developer/archived-code-guide.md.

| Bundle | Contents |
|--------|----------|
| hwsim.tar.gz | hwsim |
| cyclesim.tar.gz | cyclesim |
| plover_vm.tar.gz | plover_vm |
| rust_vm.tar.gz | crates, Cargo.toml, Cargo.lock, .cargo |
| tools.tar.gz | tools |
| hw.tar.gz | hw |
| tests_py.tar.gz | tests |
| host_toolchain.tar.gz | plover_asm, plover_cc, plover_ld, forth, kern, basic, firmware |
| verilog_sim.tar.gz | archive/verilog-sim |

## Not bundled

- build/ - gitignored sim artifacts
- docs/ - remains active
- hw-sim / rust-vm CI workflows removed