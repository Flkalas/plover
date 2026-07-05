# Download and extract xPack OpenOCD for CPLD JTAG (Windows x64).
# Idempotent: skips download/extract when openocd.exe already exists.

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Version = "0.12.0-7"
$DirName = "xpack-openocd-$Version"
$ZipName = "$DirName-win32-x64.zip"
$Url = "https://github.com/xpack-dev-tools/openocd-xpack/releases/download/v$Version/$ZipName"
$DestDir = Join-Path $Root $DirName
$Ocd = Join-Path $DestDir "bin\openocd.exe"
$ZipPath = Join-Path $Root $ZipName

if (Test-Path $Ocd) {
    Write-Host "OpenOCD already installed: $Ocd"
    exit 0
}

if (-not (Test-Path $ZipPath)) {
    Write-Host "Downloading $Url ..."
    Invoke-WebRequest -Uri $Url -OutFile $ZipPath -UseBasicParsing
}

Write-Host "Extracting to $Root ..."
Expand-Archive -Path $ZipPath -DestinationPath $Root -Force

if (-not (Test-Path $Ocd)) {
    Write-Error "openocd.exe not found after extract (expected $Ocd)"
}

Write-Host "OK: $Ocd"
