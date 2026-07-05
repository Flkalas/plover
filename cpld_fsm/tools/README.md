# CPLD FSM — JTAG tools (FT232H + OpenOCD)

Probe and (later) flash **ATF1504AS-10JU44** via Adafruit-style **FT232H** and xPack OpenOCD.

## Quick start

```powershell
cd cpld_fsm/tools
./install-wincupl.ps1    # CUPL + FIT1504 (build JED)
./install-openocd.ps1    # JTAG probe / flash
./jtag-probe.ps1
```

## WinCUPL (unpack only — no Setup.exe)

Microchip's `WinCUPL_II_v1_1_0.zip` contains **Setup.exe** (Inno Setup), not a ready `Shared\` tree.

`install-wincupl.ps1` **downloads the bundle from Microchip** when it is not already in `tools/` or `Downloads/`, then unpacks `Setup.exe` with **innounp** (file extract only).  
**Do not run Setup.exe** — installers may reboot the PC.

```powershell
cd cpld_fsm/tools
./install-wincupl.ps1   # auto-download + unpack → wincupl-ii/
```

Manual fallback (if download fails): [WinCUPL II v1.1.0](https://www.microchip.com/en-us/development-tool/WINCUPL) → copy ZIP to this folder or `Downloads`, re-run.

Setup-only files (innounp, bundle ZIP under this folder, `_wincupl_*` staging) are **removed automatically** after a successful unpack.

Requirements: **Windows**, path **without spaces**.

After install:

```powershell
cd cpld_fsm/hdl
./build-wincupl.ps1
```

## OpenOCD install

`install-openocd.ps1` downloads **xPack OpenOCD v0.12.0-7** (Windows x64) into this folder.  
Extracted tree is **gitignored** — run the script on each clone. The download ZIP is deleted after extract.

Success: `Info : JTAG tap: ATF1504AS.tap tap/device found: 0x0150403f`

## FT232H driver (Windows)

OpenOCD (libftdi) does **not** work with the default **VCP/COM** driver.

### 1. VCP installed (normal)

Device Manager shows **COM port** or **Single RS232-HS**. USB is OK, but `jtag-probe.ps1` fails with:

`LIBUSB_ERROR_NOT_SUPPORTED` / `unable to open ftdi device`

### 2. Switch to WinUSB (JTAG)

1. Install [Zadig](https://zadig.akeo.ie/) (admin).
2. **Options → List All Devices**.
3. Select **Single RS232-HS** or **FT232H**.
4. Driver: **WinUSB** → **Replace Driver**.
5. **I2C Mode = OFF** on the board.
6. **COM port disappears** — JTAG and serial cannot run at once.

### 3. Revert to serial

Zadig → same device → **FTDI VCP** / **usbser**, or reinstall FTDI CDM.

### Troubleshooting

| Symptom | Fix |
|---------|-----|
| `LIBUSB_ERROR_NOT_SUPPORTED` | WinUSB not applied |
| No JTAG ID | [wiring-flash.md](wiring-flash.md), 5 V, short wires |
| COM works, probe fails | Expected — use WinUSB for JTAG |

## Wiring

See **[wiring-flash.md](wiring-flash.md)** and `images/ft232h-breakout.svg`.

## Flash (follow-up)

After `cpld_fsm/hdl/system_ctrl.jed` exists: ATMISP JED→SVF, then OpenOCD `svf` (not in this build phase).
