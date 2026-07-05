# WinCUPL + FIT1504 build for system_ctrl.pld
# Requires: WinCUPL install, FITTERDIR -> WinCUPL\Fitters

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Repo = Resolve-Path (Join-Path $Root "..\..")
$GenPld = Join-Path $Root "system_ctrl_gen.pld"
$BasePld = Join-Path $Root "system_ctrl.pld"
$OutJed = Join-Path $Root "system_ctrl.jed"

# Fitter path limit (EleDes / Atmel fitter quirk)
$full = (Resolve-Path $Root).Path
if ($full.Length -gt 120) {
    Write-Warning "Path length $($full.Length) > 120 — move repo or use subst for fitter JED output"
}

Write-Host "Codegen ctrl_lut.inc ..."
python (Join-Path $Root "gen_ctrl_lut.py")
if (-not (Test-Path $GenPld)) {
    Write-Error "system_ctrl_gen.pld not found after codegen"
}

$Wincupl = $env:WINCUPL_DIR
if (-not $Wincupl) {
    foreach ($c in @("C:\WinCUPL", "C:\Program Files\WinCUPL", "C:\Program Files (x86)\WinCUPL")) {
        if (Test-Path $c) { $Wincupl = $c; break }
    }
}

if (-not $Wincupl) {
    Write-Host ""
    Write-Host "WINCUPL_DIR not set and WinCUPL not found."
    Write-Host "Open $GenPld in WinCUPL -> Run -> Device Dependent Compile (F9)."
    Write-Host "Set FITTERDIR to WinCUPL\Fitters if JED is not created."
    exit 0
}

$Cupl = Join-Path $Wincupl "Shared\cupl.exe"
$Fitter = Join-Path $Wincupl "Fitters\fit1504.exe"
$CuplDl = Join-Path $Wincupl "Shared\cupl.dl"

if (-not $env:FITTERDIR) {
    $env:FITTERDIR = Join-Path $Wincupl "Fitters"
}

foreach ($exe in @($Cupl, $Fitter)) {
    if (-not (Test-Path $exe)) {
        Write-Error "Missing $exe"
    }
}

$tt2 = [System.IO.Path]::ChangeExtension($GenPld, ".tt2")
$jed = [System.IO.Path]::ChangeExtension($GenPld, ".jed")

Write-Host "CUPL compile $GenPld ..."
& $Cupl -n -a -l -e -x -f -b -p -m1 -u $CuplDl F1504ISPPLCC44 $GenPld
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "FIT1504 $tt2 ..."
& $Fitter $tt2 -CUPL -device PLCC44 -tech ATF1504AS -JTAG ON
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if (Test-Path $jed) {
    Copy-Item $jed $OutJed -Force
    Write-Host "OK: $OutJed"
} elseif (Test-Path (Join-Path $env:FITTERDIR "system_ctrl_gen.jed")) {
    Copy-Item (Join-Path $env:FITTERDIR "system_ctrl_gen.jed") $OutJed -Force
    Write-Host "OK (from FITTERDIR): $OutJed"
} else {
    Write-Warning "JED not found in project dir or FITTERDIR — check fitter log"
    exit 1
}
