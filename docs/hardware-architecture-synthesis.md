# Hardware architecture synthesis (2026-06)

**Status:** **v1.0 breadboard (pre-release, 2026-06-10).** Single normative path.  
**Active normative:** [system-architecture.md](system-architecture.md) v1.0 — **CPLD GPR ~40 MC + 138×2 + 10b CW, no GAL**.

**Related:** [BOM.md](../BOM.md) · [purchase-devicesmart.md](purchase-devicesmart.md) · [purchase-2026-06-01-followup.md](purchase-2026-06-01-followup.md) · [memory-map.md](memory-map.md) · [cpld-system-controller.md](cpld-system-controller.md) · [alu-opcodes-timing.md](alu-opcodes-timing.md) · [tools/estimate_parasitics.py](../tools/estimate_parasitics.py)

---

## 1. Executive summary

| Topic | Conclusion |
|-------|------------|
| **SUB / ALU** | Gigatron-style **153+283+2's complement** matches hwsim/cyclesim. Worst-case comb delay **151 ns @ 74HC max** (not Gemini LVC ~30 ns). |
| **Purchases** | **74HC DIP** breadboard kit — not 74LVC. Phase B2 ALU ICs essentially complete; **ATF1504** ordered; **no GAL**. |
| **Control split** | **ROM** = **10b CW** (2 B/slot) + boot; **574 CW_L/CW_H** latch; **CPLD** = **GPR only** (~40 MC); **Reg_Sel** in CW B9–B8; **138×2 + 08/32/04** = `/CE` + mailbox; **574 FLG** — **no GAL**. |
| **Parasitics** | **CPLD GPR** ≈ **−20% wire hops** vs archived 574×4. **138×2** ≈ −8% on CE/map nets. **GAL rejected** (+3% hops, no 138 removal). |
| **Breadboard v1.0** | **ATF1504 GPR** + **138×2** + glue + **5×574** (PC/MBR/CW_L/CW_H/FLG) + TTL alu8. **1504 sufficient.** |
| **PCB track** | Same logic on [BOM-3v3.md](../BOM-3v3.md) (separate BOM). |
| **138 + map** | 138 = coarse `/CE`; **Mode A/B, mailbox, `$FFFC`** = discrete gates ([memory-map.md](memory-map.md)). |

**Decisions (v1.0):**

1. **ATF1504 TQFP-100** — GPR + `w_sel`/`r_sel` mux only (~36–40 MC).
2. **74HC138×2** — two-stage CE; **+1 purchase** (total 2).
3. **10b CW** — Reg_Sel packed in Flash; bus control direct from CW_L.
4. **Single bring-up** — M2a CPLD GPR → M2b 138×2 ([breadboard-wiring.md](hw-bringup/breadboard-wiring.md)).

---

## 2. SUB and ALU — Gemini archive vs implementation

Source: [archive/gemini/TTL로-가장-빠르게-SUB를-구현하는-방법…](archive/gemini/TTL로-가장-빠르게-SUB를-구현하는-방법.-기가트론은-어떻게-하고-있는지와-얼마나-걸리는지도-알려주세요..md)

### 2.1 What Gemini got right

- **Algorithm:** \(A - B = A + \overline{B} + 1\) via ripple adder.
- **Gigatron PLU:** **74HC153** (B-path + logic) + **74HC283** — no 74181.
- **153 vs XOR (86):** ~3 ns trade for unified ALU and lower chip/wiring count — matches Phase B2 (**86 removed**).
- **2 MHz target:** Comb delay is not the system bottleneck at 250 ns Execute half-period.

### 2.2 Where Gemini diverges from Plover

| Gemini assumption | Plover actual |
|-------------------|---------------|
| 74**LVC**, ~30 ns total delay | **74HC** @ 5 V, hwsim **151 ns** SUB max |
| HCT ~111 ns (153-only ~B path) | **151 ns** — extra **04_BINV** hop + **157_YBP** + HC datasheet max |
| GPR in CPLD (late conversation) | v0.1 normative: **574×4 external**; v1.3 CPLD GPR **superseded** then archived |
| Flash ×2, 16-bit control bus | **1× SST39**, **8-bit CW** @ `$4000` |
| ATF16V8B GAL required | **Not purchased**; **74HC138** available |

### 2.3 Implementation truth hierarchy

| Layer | SUB role |
|-------|----------|
| [plover_vm](../plover_vm/) | `alu8()` black box |
| [cyclesim](../cyclesim/) | Same netlist as hwsim, **zero delay**, micro-phase correctness |
| [hwsim](../hwsim/) | **151 ns** authoritative comb delay @ max |
| [hw/logic/gates.py](../hw/logic/gates.py) | Shared `eval_hc283`, `eval_alu_cmp_from_sub` |

**SUB critical path (max):**

```text
net_b0 → 04_BINV → 153_B → 283_LO/HI → 157_YBP → net_y0   → 151 ns
```

**Timing budget:** Execute half-period **250 ns** → slack **99 ns** ([alu-opcodes-timing.md](alu-opcodes-timing.md)).

**CMP flags:** `ALU_CMP_SUB` — Z = (Y==0), C_GE = `net_c_hi`; no 7485.

---

## 3. Purchase inventory vs BOM

Detailed receipts: [purchase-devicesmart.md](purchase-devicesmart.md), [purchase-2026-06-01-followup.md](purchase-2026-06-01-followup.md).

### 3.1 Actually bought (summary)

- **74HC DIP** ALU/CPU/clocks — **not 74LVC** datapath.
- **Phase B2 ALU:** 283×2, **153×8** (1차 4 + 주문 C 4), 157×8 total, 04×3, etc.
- **574×7**, **161×4**, **SST39×2**, **IS62×2**, **ATF1504×1**, **LVC245×3** (level shift only).
- **74HC138×1** (on hand) — **order +1** for v1.0 **×2** split; **74HC86/08/32×2** each — **08/32** used for CE/map glue and BEQ; **86 not used in B2 ALU**.
- **No ATF16V8B GAL** — **decided skip** (§5.3, §10).

### 3.2 Phase B2 delta vs 1st order

| Part | 1st order | Current BOM | Notes |
|------|-----------|-------------|-------|
| 74HC153 | 4 | **8** | +4 in order C |
| 74HC574 | 7 | 7 | v0.1 GPR + sequencer headroom |
| ATF1504 | 0 → +1 | 1 | 2nd/3rd order |
| 7485 | — | **0** | Never buy — CMP from SUB |

### 3.3 Still optional / BOM gaps

- CPLD **JTAG/ISP** programmer (FT232H is auxiliary).
- **PDIP Flash** (if only SOP + adapter — extra ~12 nH/pin in parasitic model).

---

## 4. Control-plane distribution

### 4.1 Principles (v1.0)

1. **ROM as law** — boot, utility, **10-bit CW** LUT (2 bytes/slot @ `$4000`) ([rom-architecture.md](rom-architecture.md), [microcode-spec.md](microcode-spec.md)).
2. **Minimal CPLD** — GPR + `w_sel`/`r_sel` only (~40 MC); **MAP_MODE** is hardware input to glue ([cpld-system-controller.md](cpld-system-controller.md)).
3. **Reg_Sel in CW** — B9–B8 latched by **574 CW_H**; table in [`reg_sel.py`](../hw/micro/reg_sel.py) packed at build time.
4. **ALU decode outside CPLD** — `alu_decode` HC gates: `ALU_OP` → `cin`, `b_sel`, `lgc*`.
5. **CE/mailbox off CPLD** — **138×2** + **08/32/04** ([memory-map.md](memory-map.md), [`mem_glue.py`](../hw/logic/mem_glue.py)).

### 4.2 Block assignment

| Block | Responsibility | Parts |
|-------|----------------|-------|
| **ROM** | Boot, program, CW @ `$4000+` (2 B/slot) | SST39 ×1 |
| **CW latch** | Flash → stable 10b @ exec edge | **574 CW_L + CW_H** |
| **Sequencer** | PC, IR, phase | 574 + 161 |
| **CPLD** | **GPR only** (R0–R3, dual read) | ATF1504 ~40 MC |
| **CE / mailbox** | RAM/ROM `/CE`, `$FF00`, Mode A/B | **138×2** + 08/32/04 |
| **ALU** | All arithmetic/logic | alu8 (14 DIP) + alu_decode |
| **Flags / branch** | Z/C; BEQ → 161 PE | **574 FLG** + 08/32 |

### 4.3 Archived split (pre-v1.0)

External-GPR and all-in-CPLD iterations are preserved under [archive/pre-v0.1/](archive/pre-v0.1/README.md) and [archive/pre-v1.0/](archive/pre-v1.0/README.md).

---

## 5. Parasitic inductance model

Tool: [tools/estimate_parasitics.py](../tools/estimate_parasitics.py)

```bash
python tools/estimate_parasitics.py
python tools/estimate_parasitics.py --detail v0.1_574_gpr
python tools/estimate_parasitics.py --detail v1.3_cpld_gpr
```

### 5.1 Constants (first-order breadboard)

| Constant | Value | Note |
|----------|-------|------|
| Wire | 10 nH/cm | Signal + return loop |
| Contact | 2 nH/hop | Breadboard spring |
| IC hop | 2.5 cm avg | Adjacent DIP |
| PLCC adapter | +8 nH/pin | ATF1504 |
| SOIC breakout | +12 nH/pin | SRAM/Flash/LVC245 |

SSO index in tool is **relative ranking**, not calibrated mV.

### 5.2 Architecture ranking (wire hops, baseline = archived v0.1 574 GPR)

| Variant | DIP | Δ hops | Δ L_sum |
|---------|-----|--------|---------|
| **v1_breadboard** (normative) | 31 | **−24%** | **−13%** |
| v1.3 CPLD GPR (archive) | 28 | **−20%** | **−17%** |
| v0.1 574 GPR (archive) | 34 | 0% | 0% |
| v0.1 + GAL (rejected) | 35 | +3% | +4% |

**Layout mitigations (no arch change):** 4× MB-102 block split; star CLK/control; **33 Ω SIP** + **0.1 µF** at every IC; CPLD **0.1 µF×4** at TQFP; place **138×2 adjacent to SRAM/Flash** for short CE stubs.

### 5.3 GAL vs 138×2 + glue — why no GAL

Two motives often cited for **ATF16V8B** were evaluated against the parasitic model and 2 MHz timing budget:

| Motive | Parasitic / timing impact | v1.0 decision |
|--------|----------------------------|-----------------|
| **138 + glue spaghetti** | Affects **CE/map scalar nets** — **moderate**; does **not** move GPR/DATA/ADDR ranking | **138×2** + **08/32/04** glue — **138 near memory** |
| **FLG + BEQ + CE in one DIP** | **FLG/BEQ** are 1b, low di/dt — **negligible** vs 8b bus SSO; CE benefit duplicated by **138×2** | **574 FLG** + µcode **BEQ** on **08/32** — no GAL |
| **GAL alongside 138** | Model **+3% wire hops** — extra DIP without removing 138 fan-out | **Do not buy GAL** |

**Net:** Parasitics justify **CPLD GPR** and **138×2**; they do **not** justify adding GAL. Glue complexity is a **wiring/debug** problem — solve with discrete gates + layout, not a third programmable device.

---

## 6. Product tiers (v1.0)

| Track | Description | BOM |
|-------|-------------|-----|
| **Breadboard v1.0** | **Normative** — CPLD GPR + 138×2 + 10b CW | [BOM.md](../BOM.md) |
| **PCB** | Same logic, SMD 3.3 V | [BOM-3v3.md](../BOM-3v3.md) |

**v1.0 breadboard split:**

- **ATF1504 (100-TQFP):** GPR + `w_sel`/`r_sel` only (~40 MC).
- **74HC138×2:** Coarse `/CE` (order **+1** → total 2).
- **74HC08/32/04:** Mailbox, Mode A/B, `/CE` glue.
- **574×5:** PC, MBR, CW_L, CW_H, FLG.
- **Reset `$FFFC`:** 157 MUX recommended until fit report.

**Do not buy:** GAL, second/larger CPLD, 7485, Flash×2 for parallel CW bus.

---

## 7. 74HC138 + ATF1504 — memory map decode

Normative map: [memory-map.md](memory-map.md). Reference logic: [cpld_decode.py](../hw/logic/cpld_decode.py).

### 7.1 What 138 can and cannot do

| Function | 138 alone? | Owner |
|----------|------------|-------|
| A15 → RAM1 vs RAM2 (coarse) | Partial | 138 Y* + enable |
| `$0000–$07FF` ROM in **Mode A** | **No** — needs **A11** + MAP | **08/32 glue** |
| `$FF00–$FFFB` **Mailbox** | **No** — compare A[15:0] | **08/32 glue** |
| `$FFFC–$FFFF` **ROM enclave** | **No** — MAP-dependent | **08/32 glue** (+ 157 MUX reset) |
| RESET → fetch `$FFFC` | **No** | **157** addr MUX (or minimal CPLD stub) |

**138 does coarse `/CE` only** — mailbox and Mode A/B live in discrete glue ([`mem_glue.py`](../hw/logic/mem_glue.py)).

### 7.2 Truth table (matches `decode_addr`)

**Mode A (MAP_MODE = 0):**

| Range | ROM_CS | RAM1 | RAM2 | MAILBOX_EN |
|-------|--------|------|------|------------|
| `$0000–$07FF` | ✓ | | | |
| `$0800–$7FFF` | | ✓ | | |
| `$8000–$FEFF` | | | ✓ | |
| `$FF00–$FFFB` | | | | ✓ |
| `$FFFC–$FFFF` | ✓ | | | |

**Mode B (MAP_MODE = 1):**

| Range | ROM_CS | RAM1 | RAM2 | MAILBOX_EN |
|-------|--------|------|------|------------|
| `$0000–$7FFF` | | ✓ | | |
| `$8000–$FEFF` | | | ✓ | |
| `$FF00–$FFFB` | | | | ✓ |
| `$FFFC–$FFFF` | | | ✓ | |

**Mailbox (both modes):**

```text
MAILBOX_EN = (A >= 16'hFF00) && (A < 16'hFFFC)
```

`$FFFC–$FFFF` is **never** mailbox — high page but excluded by **A[1:0] / compare `< 0xFFFC`**.

### 7.3 Suggested partition

```text
A[15:0] ──┬──► 08/32/04 ──► MAILBOX_EN, MAP×A11, /CE glue
          │
          ├──► ATF1504 ──► GPR q_a/q_b (REG_SEL from CW_H)
          │
          ├──► 74HC138 #2 ──► half-select (A15 / MAP)
          │
          └──► 74HC138 #1 ──► coarse Y0..Y7
                 + glue ──► RAM1_CS, RAM2_CS, ROM_CS
```

**CW fetch:** `{opcode,phase}` → Flash `$4000+` (2 bytes/slot) — separate from PC map ([memory-map.md](memory-map.md) §4).

---

## 8. Simulator and verification checklist

| Gate | Command / artifact |
|------|-------------------|
| ALU 12 opcodes | `python -m hwsim run hw/tests/alu8_full.yaml` |
| SUB 151 ns | `hw/tests/alu_b3_sub_critical.yaml` |
| CPLD GPR | `hw/tests/cpld_gpr_decode_breadboard.yaml` |
| CE / mailbox | `hw/tests/mem_decode_breadboard.yaml` · `pytest tests/test_mem_decode_breadboard.py` |
| CW pack | `python tools/verify_control_store.py` |
| Parasitic compare | `python tools/estimate_parasitics.py --detail v1_breadboard` |

---

## 9. Recommended bring-up sequence

1. **M1** — ALU B3 — [M1-alu.md](hw-bringup/M1-alu.md)
2. **M2a** — ATF1504 **GPR-only** JED — [M2a-cpld-decode.md](hw-bringup/M2a-cpld-decode.md)
3. **M2b** — 138×2 + CPLD q_a/q_b ↔ ALU — [breadboard-wiring.md](hw-bringup/breadboard-wiring.md)
4. **M3a** — 10b CW pack + dual 574 latch + Flash — [M3a-control-store.md](hw-bringup/M3a-control-store.md)
5. **M3b–M5** — fetch, boot, E2E — [hw-bringup/README.md](hw-bringup/README.md)

---

## 10. Decisions and remaining open items

### 10.1 Resolved (v1.0)

| Item | Decision |
|------|----------|
| **Breadboard GPR** | CPLD internal (~40 MC) |
| **Reg_Sel** | Flash CW B9–B8 → 574 CW_H |
| **CE / mailbox** | 138×2 + 08/32/04 glue |
| **GAL / larger CPLD** | Do not buy |
| **Bring-up** | Single v1.0 path |

### 10.2 Still open

| Item | Notes |
|------|-------|
| CPLD bitstream | Draft until MC fit report |
| Reset `$FFFC` | 157 MUX preferred until fit confirms CPLD stub |
| Flash package | SOP adapter vs PDIP |

---

## 11. Document map (avoid duplicating normative specs)

| Topic | Authoritative doc |
|-------|-------------------|
| System overview | [system-architecture.md](system-architecture.md) |
| Memory map | [memory-map.md](memory-map.md) |
| CPLD ports | [cpld-system-controller.md](cpld-system-controller.md) |
| Microcode / CW | [microcode-spec.md](microcode-spec.md) |
| ALU timing | [alu-opcodes-timing.md](alu-opcodes-timing.md) |
| Phase B2 ALU netlist | [alu8-phase-b.md](alu8-phase-b.md) |
| Shopping | [BOM.md](../BOM.md) |
| PCB target | [BOM-3v3.md](../BOM-3v3.md) |
| Gemini SUB chat (archive) | [archive/gemini/TTL…](archive/gemini/TTL로-가장-빠르게-SUB를-구현하는-방법.-기가트론은-어떻게-하고-있는지와-얼마나-걸리는지도-알려주세요..md) |

---

## Change log

| Date | Note |
|------|------|
| 2026-06-10 | Initial synthesis; parasitics tool |
| 2026-06-10 | **v1.0 breadboard unified** — 10b CW, CPLD GPR-only, gate mailbox; parasitics `v1_breadboard` |
