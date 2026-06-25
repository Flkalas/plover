# Plover ??BOM v1.1 delta (MMU add-on)

**Status:** Archived ??hardware MMU v1.1 **not adopted**.  
**Active BOM:** [BOM.md](../../../BOM.md) v1.0 breadboard only.

**Base:** [BOM.md](../../../BOM.md) v1.0 ??**do not duplicate** base lines.  
**Spec (archived):** [discrete-mmu-spec-v1.1.md](discrete-mmu-spec-v1.1.md)

v1.1 = v1.0 + **71024 MMU** + fault glue. **v2.0** (3.3 V full PCB / FPGA / mega-CPLD) is a separate track ??see [BOM-3v3.md](../../../BOM-3v3.md).

---

## Additional parts (1 set)

| 甑秳 | # | MPN | Description | Qty | ??暊 路 氇╈爜 | 牍勱碃 |
|------|---|-----|-------------|-----|-------------|------|
| MMU 路 氅旊毽?| 19b | **71024S15TYG** | 128K脳8 static RAM, 15 ns | 1 | **MMU** ??PTE + 64 KiB swap bank | 32-SOJ |
| ?疙攧??路 氚办劆 | 3b | *(SOJ-32?扗IP)* | SOJ-32 ??DIP adapter | 1 | **#19b** 牍淀寪 ?レ癌 | |
| MMU 路 glue | 11c | 74HC08 / 74HC32 / 74HC04 | AND / OR / INV | 1 each | Fault (`/NMI`), 71024 `/OE`/`/WE`, A16 | v1.0 #11b?� ?╈偘 臧�??|
| MMU 路 glue | 11d | *(optional)* 74HC157 | Quad 2:1 mux | 1 | PA[15:12] vs VA[15:12] path (layout-dependent) | |

**Unchanged from v1.0:** `#19` IS62C256脳2 (main RAM), `#14` ATF1504, `#11a` 138脳2, all ALU/clock parts.

---

## Passive adder (estimate)

| # | Part | Qty | Note |
|---|------|-----|------|
| 29 | 0.1 碌F ceramic | +4 | 71024 VCC/GND pairs |
| 29 | 10 nF ceramic | +2 | 71024 fast edge (optional per layout) |

---

## Procurement note

71024S15TYG is Renesas legacy 5 V async SRAM. Substitute only if **??5 ns** and **128K脳8** with separate `/OE`/`/WE`.
