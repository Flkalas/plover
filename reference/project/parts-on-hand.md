# v1.0 breadboard — 실구매 확정 (패키지·어댑터)

**Normative architecture:** [system-architecture.md](../hardware/system-architecture.md) v1.0  
**Shopping list:** [BOM.md](../../BOM.md) · 발주 이력 [bom-maintenance.md](bom-maintenance.md)

본 문서는 **물리 패키지, 어댑터, 보유 수량**만 기록한다.

---

## v1.0 breadboard (확정)

CPLD **2×** `ATF1504AS-10JU44` + **2×** PLCC→DIP (#15); Flash PDIP 직결; SRAM SOP28×2; LVC245 SOIC-24×3. **Dual CPLD / pipe CU.**

---

## 어댑터 역할

| BOM # | 어댑터 | Qty | 장착 대상 |
|-------|--------|-----|-----------|
| **3a** | SOP28↔DIP | 2 | IS62C256 SRAM (#19) |
| **3c** | SOIC-24↔DIP | 3 | SN74LVC8T245 (#24) |
| **15** | PLCC-44→DIP | **2** | ATF1504AS ×2 (#14 CU + DP) |

Flash (#18)는 **PDIP-32** — 빵판에 **직결** (어댑터 없음).

---

## 보유 MPN (핵심)

| BOM # | MPN | Package | Qty | 역할 |
|-------|-----|---------|-----|------|
| 14 | ATF1504AS-10JU44 | PLCC-44 | **2** | CPLD-CU + CPLD-DP (dual / pipe CU) |
| 15 | PLCC-44→DIP 어댑터 | — | **2** | CPLD 빵판 장착 |
| 18 | SST39SF010A-70-4C-PHE | PDIP-32 | 2 | 부트·program ROM (`$4000` CW reserved / unburned) |
| 19 | IS62C256AL-45ULI-TR | SOP | 2 | 64 KB RAM |
| 24 | SN74LVC8T245DWR | SOIC-24 | 3 | 5 V ↔ 3.3 V |
| 11a | 74HC138N | DIP | 1 보유 | CE decode (아래 재주문) |

상세 발주 대조: [purchase-devicesmart.md](purchase-devicesmart.md) · [purchase-2026-06-01-followup.md](purchase-2026-06-01-followup.md).

---

## 재주문

| MPN | Qty | 비고 |
|-----|-----|------|
| 74HC138N | **+1** | 총 **2** (138×2 CE tree) |

---

## ATF1504 dual CPLD I/O (desk)

| Chip | Role | Key signals |
|------|------|-------------|
| **CPLD-CU** | Pipe control | In: `opc[4:0]`, `flg_z`, `clk` · Out: strobes + G-IC `reg_we` |
| **CPLD-DP** | Datapath | In: `d_in[7:0]`, `reg_we`, `clk` · Out: `q_a` (R0) |

Detail: [cpld-system-controller.md](../hardware/cpld-system-controller.md)
| **합계** | | **~32** |

`R_SEL_A[1:0]` / `R_SEL_B[1:0]`는 CW phase 컨텍스트의 **내부 mux** — 추가 패키지 핀 아님 ([cpld-system-controller.md](../hardware/cpld-system-controller.md)).

---

## Change log

| Date | Note |
|------|------|
| 2026-06-10 | Initial — v1.0 breadboard package matrix |
