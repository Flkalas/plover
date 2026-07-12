# P12 clock candidates (desk)

**Non-normative.** Policy and OSC list: [../pe1/clock-candidates.md](../pe1/clock-candidates.md).

## P12 order of operations

1. Close pipe at **low SYS** with optimistic pack.
2. On fail → **stretch** (update sheet / `p12_stretch` model).
3. Only then raise toward **2.0 MHz**, then trial **3.6864 MHz** if BEQ slack ≥ **50 ns** measured.
4. Avoid **4.0 MHz** except stress.

Stretch before clock hope — same FE2 lab policy.

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Initial |
