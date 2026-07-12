# PE1 clock candidates and margin policy (desk)

**Status:** Research (non-normative)  
**Paths:** [timing-budget.md](timing-budget.md) (BEQ **227 ns** limiter) · [beq-lab.md](beq-lab.md)

## Margin policy (locked for PE1 research)

Use **full SYS period** latching (posedge → posedge). Do **not** budget BEQ into a half-cycle at elevated f_SYS.

| Rule | Value |
|------|------:|
| Prefer margin vs BEQ path | **≥ 20–30%** of 227 ns (**≈ 45–68 ns**) |
| Or absolute lab gate | **≥ 50 ns** measured setup slack |
| Take | **the stricter of the two** when picking f_SYS |

```text
T_min ≈ 227 ns + margin
f_max ≈ 1 / T_min
```

| Margin choice | T_min | f_SYS ceiling (desk) |
|---------------|------:|---------------------:|
| ~10% (~23 ns) | ~250 ns | **~4.0 MHz** — thin; not recommended as target |
| ~20% (~45 ns) | ~272 ns | **≲ 3.7 MHz** |
| ~30% (~68 ns) | ~295 ns | **≲ 3.4 MHz** |
| ≥ 50 ns absolute | ~277 ns | **≲ 3.6 MHz** |
| ~50% (~113 ns) | ~340 ns | **≲ 2.9 MHz** |

**Practical PE1 band after lab:** about **3.0–3.5 MHz**, or stay at **2.0 MHz** (Gi1 normative / large margin).

## Candidate oscillators

| OSC | Period | Slack vs BEQ 227 | vs policy | Note |
|-----|-------:|-----------------:|-----------|------|
| **2.000 MHz** (Gi1 ÷2 from 4 MHz) | 500 ns | **273 ns** (~120%) | Comfortable | Normative Gi1; PE1 bring-up default |
| **3.6864 MHz half-can** | **≈ 271 ns** | **≈ 44 ns** (~19%) | **Fits ~20% floor** | **Preferred elevated candidate**; UART-friendly; same HALF form factor as BOM |
| **4.000 MHz** undivided | 250 ns | **≈ 23 ns** (~10%) | Below 20% / 50 ns | Desk-possible but **not** margin target |
| 3.6864 ÷ 2 = 1.8432 MHz | ≈ 543 ns | large | Very safe | Slow; debug fallback |

### 3.6864 MHz half-type — recommendation

**Good PE1 trial clock:** margin sits on the **20%** line; better than raw 4 MHz; HC-49 half matches kit style; classic baud-rate crystal.

Lab must still **measure BEQ slack** ([beq-lab.md](beq-lab.md)); desk 44 ns is slightly under the **50 ns** absolute gate — pass/fail is the scope, not the datasheet sum.

## 4 MHz SYS?

**Conditional:** only if full-period latching and measured BEQ slack remains acceptable. Desk slack ~23 ns = **~10%** — treat as stress, not the design point.

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Margin policy; 3.6864 / 4 MHz candidates |
