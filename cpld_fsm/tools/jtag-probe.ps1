# Probe ATF1504AS on Adafruit FT232H via OpenOCD (xpack in tools/).
# Prereq: I2C Mode OFF; CPLD wired; for libftdi build use WinUSB (Zadig) not VCP/COM.

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Ocd = Join-Path $Root "xpack-openocd-0.12.0-7\bin\openocd.exe"
$Scripts = Join-Path $Root "xpack-openocd-0.12.0-7\openocd\scripts"

if (-not (Test-Path $Ocd)) {
    Write-Error "openocd.exe not found. Run install-openocd.ps1 in $Root"
}

& $Ocd -s $Scripts `
    -f interface/ftdi/um232h.cfg `
    -c "adapter speed 400" `
    -c "transport select jtag" `
    -c "jtag newtap ATF1504AS tap -irlen 3 -expected-id 0x0150403f" `
    -c init `
    -c shutdown
