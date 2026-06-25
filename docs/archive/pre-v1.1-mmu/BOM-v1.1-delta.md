# Plover — BOM v1.1 delta (MMU add-on)

**Base:** [BOM.md](BOM.md) v1.0 breadboard — **do not duplicate** base lines.  
**Normative:** [discrete-mmu-spec-v1.1.md](docs/hardware/discrete-mmu-spec-v1.1.md)

v1.1 = v1.0 + **71024 MMU** + fault glue. **v2.0** (3.3 V full PCB / FPGA / mega-CPLD) is a separate track — see [BOM-3v3.md](BOM-3v3.md).

---

## Additional parts (1 set)

| 구분 | # | MPN | Description | Qty | 역할 · 목적 | 비고 |
|------|---|-----|-------------|-----|-------------|------|
| MMU · 메모리 | 19b | **71024S15TYG** | 128K×8 static RAM, 15 ns | 1 | **MMU** — PTE + 64 KiB swap bank | 32-SOJ |
| 인프라 · 배선 | 3b | *(SOJ-32→DIP)* | SOJ-32 ↔ DIP adapter | 1 | **#19b** 빵판 장착 | |
| MMU · glue | 11c | 74HC08 / 74HC32 / 74HC04 | AND / OR / INV | 1 each | Fault (`/NMI`), 71024 `/OE`/`/WE`, A16 | v1.0 #11b와 합산 가능 |
| MMU · glue | 11d | *(optional)* 74HC157 | Quad 2:1 mux | 1 | PA[15:12] vs VA[15:12] path (layout-dependent) | |

**Unchanged from v1.0:** `#19` IS62C256×2 (main RAM), `#14` ATF1504, `#11a` 138×2, all ALU/clock parts.

---

## Passive adder (estimate)

| # | Part | Qty | Note |
|---|------|-----|------|
| 29 | 0.1 µF ceramic | +4 | 71024 VCC/GND pairs |
| 29 | 10 nF ceramic | +2 | 71024 fast edge (optional per layout) |

---

## Procurement note

71024S15TYG is Renesas legacy 5 V async SRAM. Substitute only if **≤15 ns** and **128K×8** with separate `/OE`/`/WE`.
