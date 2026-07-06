# Feasibility matrix — implementation paths

**Parent:** [README.md](README.md) · Pins: [pin-budget.md](pin-budget.md) · MC: [mc-estimate.md](mc-estimate.md)

**Bring-up gate (all paths):** WinCUPL **Design fits** on target device(s).

---

## Summary table

| ID | Strategy | DP pins | DP MC (desk) | ISA scope | BOM vs rev G | Verdict |
|----|----------|---------|--------------|-----------|--------------|---------|
| **P0** | Naive `r_sel_a/b` on G-IC (+4) | **35/32 FAIL** | ~46–56 likely PASS | Full 4-GPR + STR | 2×1504 | **FAIL pins** |
| **P1** | Bus-TDM `q_bus` + 574 A + `r_sel` ([p1-bus-tdm/](p1-bus-tdm/)) | **28/32 PASS** | ~48–58 likely | Full 4-GPR | 2×1504 +1×574 | **Pins PASS; timing conditional** |
| **P1M1** | P1 + M1 dual 574 + 2-half ph2 ([p1m1-dual574/](p1m1-dual574/)) | **29/32 PASS** | ~50–60 likely | Full 4-GPR; ph2 **500 ns** | 2×1504 +2×574 | **Pins PASS; timing PASS (desk)** |
| **P1-old** | G-IC time-mux / `d_in` share only (no q merge) | 33–42 TBD | TBD | Full 4-GPR | 2×1504 | Superseded by bus-TDM study |
| **P2** | STR-only; fixed ALU reads | **31/32 PASS** | ~22–32 | Partial — STR + R3? | 2×1504 | **Conditional PASS** |
| **Gi1** | AC + MBR→B; R0 only ([gi1-ac-mbr/](gi1-ac-mbr/)) | **17/32 PASS** | ~10–18 | AC-centric; **no TFR** | 2×1504, **3×574** | **Timing PASS @ 250 ns (desk)** |
| **P3** | External GPR (fit-study A1) | ≤32 PASS | ~20–30 on DP | Full | **+574×N** | **PASS** (cost) |
| **P4** | ATF1508 (fit-study C2) | >>32 | headroom | Full | **Different CPLD** | **PASS** (BOM change) |
| **P5** | Hidden TMP (TFR-tmp-2op) | 31/32 PASS | +8 FF | 3 visible + scratch | 2×1504 | **PASS** — not 4 visible GPR |

---

## P0 — Naive dual read select

**Description:** User proposal verbatim — 4×FF, `r_sel_a[1:0]`, `r_sel_b[1:0]`, `w_sel`, `reg_we`, xfer/TFR, full `q_a`/`q_b`.

| Gate | Result |
|------|--------|
| Pins | **FAIL +3** |
| MC | Likely PASS |
| ISA | Full v1.1 vision |
| cyclesim | Full `dp.py` mux |

**Recommendation:** Document as **not implementable** on ATF1504 DP without pin trade. Use as PLD spike to confirm fitter pin overflow.

---

## P1 — Bus-TDM + clock division

**Description:** Merge `q_a`/`q_b` → **`q_bus[7:0]`**; T1/T2 @ 4 MHz within 250 ns; **574** latches ALU A; `r_sel_a/b` on G-IC; optional C0–C4 clock trees.

**Detail:** [p1-bus-tdm/REPORT.md](p1-bus-tdm/REPORT.md) · [pin-map.md](p1-bus-tdm/pin-map.md) · [timing-cross-domain.md](p1-bus-tdm/timing-cross-domain.md)

| Gate | Result |
|------|--------|
| Pins (DP) | **PASS 28/32** |
| MC | ~48–58 desk likely PASS |
| Timing | **Conditional** — ADD/INC fail single 250 ns; need **M1** or **M2** |
| BOM | +1×574 (ALU A); C1 may −74HC74 |

**Recommendation:** Preferred path for **full 4-GPR + selectable read** on 2×1504 after timing mitigation chosen. Spike with **C0** clock + [p1_dp_bus_tdm PLD](variants/p1_dp_bus_tdm/system_ctrl.pld). **Integrated timing closure:** see [P1M1](p1m1-dual574/SUMMARY-REPORT.md) (P1 + M1 dual 574).

---

## P1M1 — P1 + M1 dual 574 (integrated)

**Description:** Merge P1 bus-TDM with M1 operand latching — **574×2** on ALU A/B; ph2 execute **fetch 250 ns + compute 250 ns**; `op_fetch` gates `q_bus` TDM.

**Detail:** [p1m1-dual574/SUMMARY-REPORT.md](p1m1-dual574/SUMMARY-REPORT.md) · [pin-map.md](p1m1-dual574/pin-map.md) · [timing-closed.md](p1m1-dual574/timing-closed.md)

| Gate | Result |
|------|--------|
| Pins (DP) | **PASS 29/32** (+`alu_b_le`) |
| MC | ~50–60 desk likely PASS |
| Timing | **PASS (desk)** — ADD @ 383 ns vs 500 ns |
| BOM | **5×574** (+2 vs rev G) |

**Recommendation:** Preferred **full 4-GPR** path when timing must close on breadboard without FSM-only M2. Spike [p1m1_dp PLD](variants/p1m1_dp/system_ctrl.pld).

---

## P2 — STR-only (minimal delta)

**Description:** Keep `q_a←R0`, `q_b←R1`. Add **R3** optional. **STR0..STR3** drives bus from selected reg via **`src[1:0]` during `Y_OE`** (see [str-encoding-options.md](str-encoding-options.md) Option A).

| Gate | Result |
|------|--------|
| Pins | **31/32** if no extra wires |
| MC | +8 FF if R3; +4:1 store mux internal to `q_a` path only |
| ISA | Eliminates Fibonacci TFR; not full ALU `r_sel` |
| User vision match | **Partial** |

**Recommendation:** Best **first hardware experiment** on existing breadboard BOM if goal is drop TFR traffic before full regfile.

---

## Gi1 — Gigatron-style AC + MBR operand (Gi1 full)

**Description:** Single **R0 (AC)** in CPLD-DP; **`net_mbr → ALU B`**; ADD/CMP writeback **R0**; **TFR opcodes removed**; ph2 **250 ns** desk closed.

**Detail:** [gi1-ac-mbr/SUMMARY-REPORT.md](gi1-ac-mbr/SUMMARY-REPORT.md) · [pin-map.md](gi1-ac-mbr/pin-map.md) · [timing-closed.md](gi1-ac-mbr/timing-closed.md)

| Gate | Result |
|------|--------|
| Pins (DP) | **PASS 17/32** |
| MC | ~10–18 desk |
| Timing | **PASS** — ADD @ 133 ns vs 250 ns |
| ISA | AC-centric; **no TFR**; not 4-GPR |
| BOM | **unchanged** 3×574 |

**Recommendation:** Preferred when **2 MHz timing certainty** beats 4-GPR / TFR. Spike [gi1_dp PLD](variants/gi1_dp/system_ctrl.pld) + MBR→B wire.

---

## P3 — External GPR (A1 lineage)

**Description:** GPR in **74HC574×4**; CPLD-DP or CU drives `reg_we`/`w_sel`/bus only.

| Gate | Result |
|------|--------|
| Pins | CPLD **PASS** (fit-study A1+A2: 32/32) |
| MC | Lower on CPLD |
| BOM | +3–4 DIP vs rev G |

**Recommendation:** Full 4-GPR + selectable read if breadboard wire budget acceptable. See `fit-study/variants/a1_a2_a3/` in archive.

---

## P4 — ATF1508

**Description:** Migrate to higher I/O device (fit-study C2).

| Gate | Result |
|------|--------|
| Pins | PASS |
| MC | 128 MC rating |
| BOM | New part + adapter; WinCUPL device string |

**Recommendation:** Long-term if staying single-chip datapath; out of v1.0 breadboard stock.

---

## P5 — Hidden TMP (archive)

**Description:** `fit-study/tfr-isa-variants.md` **TFR-tmp-2op** — R0–R2 visible, **TMP** scratch, 2 micro-ops per transfer.

| Gate | Result |
|------|--------|
| Pins | PASS on rev G budget |
| User 4 visible GPR | **No** |

**Recommendation:** Cite as prior art; not a match for stated goal.

---

## Ranking for v1.0 breadboard (2× ATF1504AS-10JU44)

| Rank | Path | Rationale |
|------|------|-----------|
| 1 | **Gi1** AC+MBR | **250 ns timing PASS**; max pin/MC headroom; ISA change |
| 1b | **P2** + STR0..3 | Pins PASS; store-from-R2; smaller ISA delta than Gi1 |
| 2 | **P1 bus-TDM** | Full vision; pins proven; timing needs M1/M2 |
| 2b | **P1M1** | P1 + M1 integrated; pins + desk timing PASS |
| 3 | **P3** | Full vision with BOM cost |
| — | **P0** | **Ruled out** (pins) |
| — | **P4** | Requires new silicon |
| — | **P5** | Wrong register model |

---

## Verification matrix

| Path | Desk pin | Desk MC | WinCUPL | cyclesim | Breadboard |
|------|----------|---------|---------|----------|------------|
| P0 | Done FAIL | Done | Spike PLD | — | — |
| P1 | Done PASS | Est. ~48–58 | Spike PLD | — | — |
| P1M1 | Done PASS | Est. ~50–60 | Spike PLD | — | — |
| P2 | Done PASS | Est. | TBD | TBD | TBD |
| Gi1 | Done PASS | Est. ~10–18 | Spike PLD | — | — |
| P3 | Archive PASS | Archive | Archive | — | — |
| P4 | Archive | Archive | — | — | — |
| P5 | Archive | Archive | — | — | — |

---

## Cross-reference — archive fit-study

| Variant | Report | Relevance |
|---------|--------|-----------|
| G dual | `REPORT-g-dual.md` | Production baseline |
| A1 | `variants/a1_a2_a3/` | P3 external GPR |
| E1 TFR-tmp | `tfr-isa-variants.md` | P5 |
| C2 ATF1508 | `pin-budget-variants.md` | P4 |

Restore: `tar -xzf archive/fit-study-gpr-fsm.tar.gz` (local only; not copied into `research/` per plan).
