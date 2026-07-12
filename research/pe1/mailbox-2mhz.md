# PE1 + mailbox @ 2 MHz (desk deepen)

**Status:** Research (non-normative)  
**Build:** PE1 · [timing-budget.md](timing-budget.md) · [SUMMARY-REPORT.md](SUMMARY-REPORT.md)  
**Protocol:** [mailbox-protocol.md](../../reference/copro/mailbox-protocol.md)

## Question

With **PE1 pipe latches/buffers** added, can **all normative mailbox jobs** still **close timing** at **`CLK_SYS = 2.0 MHz`**, without a separate vFDD fast path?

## Verdict (desk): **Conditional Go**

| Claim | Desk |
|-------|------|
| Timing closure @ 2 MHz for mailbox R/W | **Yes** if RP GPIO responds within **~80 ns** desk assumption — path **170 ns**, slack **330 ns @ 500 ns** / **80 ns @ 250 ns** |
| Limiter at 2 MHz | Still **BEQ** (stress), **not** mailbox |
| Need vFDD alternate path for **timing**? | **No** |
| Need alternate path for **higher B/s**? | Only if product wants **> ~0.22–0.29 MB/s** CPU copy ([model/mailbox_copy_bps.py](model/mailbox_copy_bps.py)) |

**PE1 does not make mailbox “fast.”** It must only **not break** 2 MHz MMIO after latch adds. Copy stays DATA-bound (PE1 ≈ FE2 B/s).

## Assumptions (explicit)

1. Primary budget = **full SYS period 500 ns** (PE1 IF∥EX).
2. RP2350 mailbox shadow responds in **≤ 80 ns** from OE/offset stable (lab gate — softest number).
3. Mode A breadboard includes **LVC245** on the copro tap.
4. `Busy` / SD / VDU work time is **software wait**, not an EX combinational path.

## Job matrix — all mailbox traffic

| Job | CPU ops | Path class | 2 MHz ns OK? | Soft wait |
|-----|---------|------------|--------------|-----------|
| STATUS poll | `LDIO $00` | mailbox read | **Yes** (desk) | spin until DataReady / not Busy |
| CMD / PARAM / AUX | `STIO` | mailbox write | **Yes** | — |
| Buffer byte in/out | `LDIO` / `STIO` | mailbox | **Yes** | — |
| Boot copy 1 B → RAM | `LDIO` + `STA16` | mailbox **then** SRAM | **Yes** both EX paths | after DataReady |
| VDU / GFX / APU / HID cmds | `STIO` (+ buffer fill) | mailbox | **Yes** | Busy → silent drop (protocol) |
| vFDD READ sector | CMD + poll + N× copy | mailbox + SRAM | **Yes** timing | **Busy** dominates wall time |

## Separating two meanings of “possible”

| Meaning | Answer @ 2 MHz + PE1 latches |
|---------|------------------------------|
| **Timing closure** — each MMIO/SRAM edge meets setup | **Conditional Go** (RP ≤ 80 ns) |
| **Throughput** — feel as fast as DMA/shared VRAM | **No claim** — ~222 KB/s Gi1 / ~286 KB/s FE2·PE1 copy ceiling |
| **vs Apple II FDD** | Different bottleneck; mailbox not uniquely worse for floppy-scale I/O |

## Lab gates

1. Measure `MAILBOX_EN` → D valid (RP drive) on `LDIO` at 2 MHz.
2. If >80 ns, update [timing-budget.md](timing-budget.md) and re-check slack @ 250 ns.
3. Boot unrolled copy smoke: 248× `LDIO`/`STA16` after DataReady (functional; bandwidth is model-only).

## Change log

| Date | Note |
|------|------|
| 2026-07-13 | Initial mailbox @ 2 MHz deepen |
