# Subset C (S5)

The v0.1 Subset-C compiler is a **bootstrap tool** used to generate small Plover programs.
It is intentionally tiny and grows only as needed for kernel bring-up.

## Static allocation (normative target)

v1.0 breadboard has no hardware stack or frame pointer. **S5 Subset C** therefore targets **static allocation**: locals and parameters live in **fixed RAM cells** at compile time; **unbounded recursion** is out of scope. See [plover-whitepaper.md](../project/plover-whitepaper.md) §2.3.1.

## Supported (v0.1)

- `int main(void) { return <int>; }`
- `int main(void) { return add(<int>, <int>); }` (built-in `add` pattern)

## Output

- Subset C → Plover asm text → `plover_asm` → `.sram.hex`

## CLI

```bash
python -m plover_cc hw/fixtures/sw/cc_smoke.c -o hw/fixtures/sram/cc_smoke.sram.hex
```

## Tests

- `tests/test_plover_cc.py`

