# Dual CPLD JTAG daisy chain (v1.0)

**Device:** ATF1504AS PLCC-44 — ISP pins **7=TDI, 13=TMS, 32=TCK, 38=TDO**

---

## Chain order

Programmer → **CPLD-CU** → **CPLD-DP** → programmer

```text
Programmer TDI ──► CU pin 7
CU pin 38 (TDO) ──► DP pin 7 (TDI)
DP pin 38 (TDO) ──► Programmer TDO

TCK pin 32 ── parallel to both CPLDs
TMS pin 13 ── parallel to both CPLDs
```

---

## Procedure

1. Power both CPLDs at **5 V**; **0.1 µF** decoupling per chip.
2. Keep daisy-chain wires **≤ 10 cm**.
3. Program **CU JED first**, then **DP** (CU is chain position 0).
4. Run mode: JTAG pins idle; G-IC uses DP pins 12, 14, 16–19 (not 7/38).

---

## BOM

2× ATF1504 (#14), 2× PLCC adapter (#15). See [BOM.md](../project/BOM.md).
