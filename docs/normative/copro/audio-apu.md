# Audio APU v0.1 (4ch PSG)

**Source decision record:** [archive/gemini/Plover-APU-설계-질의-및-결정.md](../archive/gemini/Plover-APU-설계-질의-및-결정.md)  
**Related:** [mailbox-protocol.md](mailbox-protocol.md) · [rp2350-coprocessor.md](rp2350-coprocessor.md)

Normative **4-channel PSG** on RP2350 Core0. CPU controls audio **only via Mailbox** (`MB_CMD` `0x50–0x53`); no audio buffer on the 64 KiB CPU map. **PCM streaming is v0.2.**

---

## 1. Architecture

| Item | Value |
|------|-------|
| Channels | **4** — ch0–2 **square**, ch3 **noise** (LFSR) |
| Internal mix | **22.05 kHz**, **8-bit mono** |
| Clock constant | **`f_clk = 44_100 Hz`** |
| Period formula | `f_out = f_clk / (2 × period)` (`period ≥ 1`) |
| VSYNC | **Independent** — APU sample clock ≠ VDU 30 Hz |
| Control | Mailbox only — **reject** SRAM `0x7FEx` scan model |

---

## 2. RP2350 responsibilities

| Task | Core | Notes |
|------|------|-------|
| PSG mix @ 22.05 kHz | **Core0** | Shared with vFDD SPI, USB/HID (future) |
| Param queue | Core0 | ≤ **1 KiB** staged writes before `APU_CH_SYNC` |
| PWM output | Core0 GPIO | **PWM + RC filter** → 3.5 mm jack (bring-up) |
| VDU / HSTX | Core1 | No APU on Core1 (bus/render contention) |

**v0.1 constraint:** During vFDD **Busy**, APU commands are **silent dropped** (not queued).

---

## 3. Error policy (APU-specific)

Unlike VDU/GFX, APU uses **silent drop**:

- vFDD Busy, invalid channel/wave, queue full → command **ignored**
- **No `ST_ERROR`** for APU
- Poll **`APU_READY`** (MB_STATUS bit3) before issuing APU commands (optional; drops are safe)

---

## 4. Mailbox commands

See [mailbox-protocol.md](mailbox-protocol.md) §2.4.

| CMD | Name | Summary |
|-----|------|---------|
| `0x50` | APU_SET_CTRL | Master volume, mute flag |
| `0x51` | APU_CH_WRITE | Stage one channel (applied on SYNC) |
| `0x52` | APU_CH_SYNC | Commit staged channels |
| `0x53` | APU_CH_OFF | Immediate mute one channel |

**Reserved:** `0x54–0x5F` future PCM/extension. HID: [input-hid.md](input-hid.md) (`0x40–0x43`).

---

## 5. VM / bring-up

| Layer | v0.1 |
|-------|------|
| logic VM (developer) | [`ApuState`](../logic VM/memory/apu.py) — register + optional `mix_samples()` for tests |
| Host speaker | **Deferred v0.2** |
| Forth / PL-DOS | `BEEP ( period duration -- )` minimal API |
| Gate | `apu_smoke.pls` + VM register assert; hardware 1 kHz on oscilloscope |

---

## Change log

| Date | Note |
|------|------|
| 2026-06-08 | v0.1 normative: 4ch PSG, Mailbox 0x50–0x53 |
