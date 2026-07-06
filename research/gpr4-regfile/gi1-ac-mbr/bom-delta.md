# Gi1 BOM and silicon delta

**Parent:** [README.md](README.md)  
**Normative BOM:** [reference/project/BOM.md](../../../reference/project/BOM.md) — **not modified**

---

## IC count

| IC | rev G | **Gi1** | Δ |
|----|-------|---------|---|
| ATF1504AS-10JU44 | 2 | 2 | 0 |
| 74HC574 | **3** (PC/MBR/FLG) | **3** | **0** |
| 74HC74 (÷2) | 1 | 1 | 0 |
| 4 MHz OSC | 1 | 1 | 0 |
| 74HC244 (optional) | 0 | 0–1 | optional MBR fanout |

**No** extra operand 574 (vs P1 +1, P1M1 +2).

---

## 574 roles (unchanged)

| # | Role |
|---|------|
| 1 | PC (+161) |
| 2 | IR / opcode path |
| 3 | **MBR** — **Gi1: also ALU B source** |
| — | FLG |

---

## CPLD-DP resources (desk)

| Resource | rev G | Gi1 | Δ |
|----------|-------|-----|---|
| GPR FF | 24 | **8** | **−16** |
| 4:1 read mux | 0 (fixed) | 0 | 0 |
| TFR xfer mux | 4:1 × 8 | **0** | −8 FF equiv |
| `w_sel` decode | 3-term | **0** | −3 |
| I/O pins | 31 | **17** | **−14** |
| MC estimate | ~18–28 | **~10–18** | **−8~10** |

---

## Wiring delta (lab)

| Action | Detail |
|--------|--------|
| **Remove** | CPLD `q_b0..7` → ALU B |
| **Add** | `net_mbr0..7` → `net_b0..7` |
| **JED** | DP + CU reprogram (Gi1 PLD forks) |

Power / area: **fewer FF** in DP; no extra DIP.

---

## Related

- [pin-map.md](pin-map.md)
- [SUMMARY-REPORT.md](SUMMARY-REPORT.md)
