# Unpack WinCUPL for CPLD CUPL/FIT1504 builds — no Setup.exe, no installer, no reboot.
# Idempotent: skips when Shared\cupl.exe already exists under wincupl-ii\.
#
# WinCUPL_II_v1_1_0.zip from Microchip contains Setup.exe (Inno Setup), not a ready tree.
# This script unpacks Setup.exe with innounp (file extract only).

param(
    [string]$ZipPath = "",
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$DestDir = Join-Path $Root "wincupl-ii"
$Cupl = Join-Path $DestDir "Shared\cupl.exe"
$Fitter = Join-Path $DestDir "Fitters\fit1504.exe"

$InnounpZipUrl = "https://rathlev-home.de/tools/download/innounp-2.zip"
$InnounpDir = Join-Path $Root "innounp-2"

$BundleZipUrl = "https://ww1.microchip.com/downloads/aemDocuments/documents/MPD/SoftwareLibrary/WinCUPL_II_v1_1_0.zip"
$BundleZipFile = "WinCUPL_II_v1_1_0.zip"

$BundleZipNames = @(
    $BundleZipFile,
    "WinCUPL_II_v1.1.0.zip",
    "wincupl.zip"
)

$DownloadPage = "https://www.microchip.com/en-us/development-tool/WINCUPL"

function Remove-WincuplSetupTemp {
    param([string]$Root)
    $paths = @(
        "innounp-2",
        "innounp-2.zip",
        "innounp050.rar",
        "innoextract-1.9",
        "innoextract-1.9-windows.zip",
        "7zr.exe"
    )
    foreach ($name in $paths) {
        $p = Join-Path $Root $name
        if (Test-Path $p) {
            Remove-Item $p -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "Removed setup temp: $name"
        }
    }
    foreach ($name in $BundleZipNames) {
        $p = Join-Path $Root $name
        if (Test-Path $p) {
            Remove-Item $p -Force -ErrorAction SilentlyContinue
            Write-Host "Removed setup temp: $name"
        }
    }
    Get-ChildItem -Path $Root -Directory -Filter "_wincupl_*" -ErrorAction SilentlyContinue | ForEach-Object {
        Remove-Item $_.FullName -Recurse -Force
        Write-Host "Removed setup temp: $($_.Name)"
    }
}

function Find-WincuplRoot {
    param([string]$Base)
    if (Test-Path (Join-Path $Base "Shared\cupl.exe")) { return $Base }
    $app = Join-Path $Base "{app}"
    if (Test-Path (Join-Path $app "Shared\cupl.exe")) { return $app }
    foreach ($d in Get-ChildItem -Path $Base -Directory -ErrorAction SilentlyContinue) {
        if (Test-Path (Join-Path $d.FullName "Shared\cupl.exe")) { return $d.FullName }
    }
    return $null
}

function Ensure-Innounp {
    $exe = Get-ChildItem -Path $InnounpDir -Filter "innounp.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($exe) { return $exe.FullName }
    $zip = Join-Path $Root "innounp-2.zip"
    Write-Host "Downloading innounp (Inno Setup unpacker) ..."
    Invoke-WebRequest -Uri $InnounpZipUrl -OutFile $zip -UseBasicParsing
    Expand-Archive -Path $zip -DestinationPath $InnounpDir -Force
    $exe = Get-ChildItem -Path $InnounpDir -Filter "innounp.exe" -Recurse | Select-Object -First 1
    if (-not $exe) { throw "innounp.exe not found after download" }
    return $exe.FullName
}

function Resolve-BundleZip {
    if ($ZipPath -and (Test-Path $ZipPath)) { return (Resolve-Path $ZipPath).Path }
    foreach ($name in $BundleZipNames) {
        $candidate = Join-Path $Root $name
        if (Test-Path $candidate) { return $candidate }
    }
    foreach ($name in $BundleZipNames) {
        $candidate = Join-Path $env:USERPROFILE "Downloads\$name"
        if (Test-Path $candidate) { return $candidate }
    }
    return $null
}

function Ensure-BundleZip {
    $existing = Resolve-BundleZip
    if ($existing) { return $existing }

    $dest = Join-Path $Root $BundleZipFile
    Write-Host "Downloading WinCUPL II v1.1.0 from Microchip ..."
    Write-Host "  $BundleZipUrl"
    try {
        Invoke-WebRequest -Uri $BundleZipUrl -OutFile $dest -UseBasicParsing
    } catch {
        throw "WinCUPL download failed: $($_.Exception.Message)`nManual: $DownloadPage"
    }
    if (-not (Test-Path $dest)) { throw "WinCUPL download produced no file: $dest" }
    $size = (Get-Item $dest).Length
    if ($size -lt 1MB) { throw "WinCUPL download looks too small ($size bytes): $dest" }
    Write-Host "Saved $BundleZipFile ($([math]::Round($size / 1MB, 1)) MB)"
    return $dest
}

function Unpack-FromBundleZip {
    param([string]$Archive)
    Write-Host "Unpacking $Archive ..."
    $staging = Join-Path $Root "_wincupl_bundle"
    if (Test-Path $staging) { Remove-Item $staging -Recurse -Force }
    New-Item -ItemType Directory -Path $staging | Out-Null
    Expand-Archive -Path $Archive -DestinationPath $staging -Force

    $setup = Get-ChildItem -Path $staging -Filter "Setup.exe" -Recurse | Select-Object -First 1
    if ($setup) {
        Unpack-SetupExe -SetupPath $setup.FullName
        Remove-Item $staging -Recurse -Force
        return
    }

    $found = Find-WincuplRoot $staging
    if ($found) {
        Publish-WincuplTree -Source $found
        Remove-Item $staging -Recurse -Force
        return
    }

    Remove-Item $staging -Recurse -Force
    throw "Neither Setup.exe nor Shared\cupl.exe found in $Archive"
}

function Unpack-SetupExe {
    param([string]$SetupPath)
    Write-Host "Unpacking Setup.exe with innounp (not running installer): $SetupPath"
    $innounp = Ensure-Innounp
    $staging = Join-Path $Root "_wincupl_unpack"
    if (Test-Path $staging) { Remove-Item $staging -Recurse -Force }
    New-Item -ItemType Directory -Path $staging | Out-Null
    & $innounp -x -y "-d$staging" $SetupPath | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "innounp failed (exit $LASTEXITCODE)" }
    $found = Find-WincuplRoot $staging
    if (-not $found) { throw "Shared\cupl.exe not found after innounp unpack" }
    Publish-WincuplTree -Source $found
    Remove-Item $staging -Recurse -Force
}

function Publish-WincuplTree {
    param([string]$Source)
    if (Test-Path $DestDir) { Remove-Item $DestDir -Recurse -Force }
    New-Item -ItemType Directory -Path $DestDir | Out-Null
    Copy-Item -Path (Join-Path $Source "*") -Destination $DestDir -Recurse -Force
}

if ((Test-Path $Cupl) -and (Test-Path $Fitter) -and -not $Force) {
    Remove-WincuplSetupTemp -Root $Root
    Write-Host "WinCUPL already ready: $DestDir"
    Write-Host "  cupl.exe    -> $Cupl"
    Write-Host "  fit1504.exe -> $Fitter"
    exit 0
}

if ($DestDir -match " ") {
    throw "WinCUPL path must not contain spaces: $DestDir"
}

$bundle = Ensure-BundleZip
Unpack-FromBundleZip -Archive $bundle

if (-not (Test-Path $Cupl)) { throw "Missing $Cupl after unpack" }
if (-not (Test-Path $Fitter)) { throw "Missing $Fitter after unpack" }

Remove-WincuplSetupTemp -Root $Root

Write-Host ""
Write-Host "OK: WinCUPL unpacked to $DestDir (no installer run)"
Write-Host "  WINCUPL_DIR=$DestDir"
Write-Host "  FITTERDIR=$(Join-Path $DestDir 'Fitters')"
Write-Host ""
Write-Host "Next: restore HDL (archive/cpld-rev-g-hdl.tar.gz) then cd cpld/hdl && ./build-wincupl.ps1"
