# WinCUPL + FIT1504 build for rev G dual CPLD (CU + DP)
# Requires: WinCUPL install, FITTERDIR -> WinCUPL\Fitters

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Repo = Resolve-Path (Join-Path $Root "..\..")

Write-Host "Codegen ctrl_lut.inc ..."
python (Join-Path $Root "gen_ctrl_lut.py")
if (-not (Test-Path (Join-Path $Root "system_ctrl_cu_gen.pld"))) {
    Write-Error "system_ctrl_cu_gen.pld not found after codegen"
}

$ToolsWincupl = Join-Path $Repo "cpld_fsm\tools\wincupl-ii"
$Wincupl = $env:WINCUPL_DIR
if (-not $Wincupl -and (Test-Path (Join-Path $ToolsWincupl "Shared\cupl.exe"))) {
    $Wincupl = $ToolsWincupl
}
if (-not $Wincupl) {
    foreach ($c in @("C:\WinCUPL", "C:\Wincupl", "C:\Program Files\WinCUPL", "C:\Program Files (x86)\WinCUPL")) {
        if (Test-Path $c) { $Wincupl = $c; break }
    }
}

if (-not $Wincupl) {
    Write-Host ""
    Write-Host "WINCUPL_DIR not set and WinCUPL not found."
    Write-Host "Open system_ctrl_cu_gen.pld and system_ctrl_dp_gen.pld in WinCUPL -> F9."
    exit 0
}

$Cupl = Join-Path $Wincupl "Shared\cupl.exe"
$Fitter = Join-Path $Wincupl "Fitters\fit1504.exe"
$CuplDl = Join-Path $Wincupl "Shared\cupl.dl"

if (-not $env:FITTERDIR) {
    $env:FITTERDIR = Join-Path $Wincupl "Fitters"
}

foreach ($exe in @($Cupl, $Fitter)) {
    if (-not (Test-Path $exe)) { Write-Error "Missing $exe" }
}

function Build-OnePld {
    param([string]$Stem)
    $GenPld = Join-Path $Root "${Stem}_gen.pld"
    $OutJed = Join-Path $Root "${Stem}.jed"
    $tt2 = [System.IO.Path]::ChangeExtension($GenPld, ".tt2")
    $jed = [System.IO.Path]::ChangeExtension($GenPld, ".jed")
    $fitLog = Join-Path $Root "${Stem}_fit_last.log"

    Write-Host "CUPL compile $GenPld ..."
    & $Cupl -n -a -l -e -x -f -b -p -m1 -u $CuplDl F1504ISPPLCC44 $GenPld
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host "FIT1504 $tt2 ..."
    & $Fitter $tt2 -CUPL -device PLCC44 -tech ATF1504AS -JTAG ON 2>&1 | Tee-Object -FilePath $fitLog
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    $fitText = Get-Content $fitLog -Raw -ErrorAction SilentlyContinue
    if ($fitText -notmatch "Design fits") {
        Write-Error "Fitter did not report Design fits for $Stem — see $fitLog"
    }

    if (Test-Path $jed) {
        Copy-Item $jed $OutJed -Force
        Write-Host "OK: $OutJed"
    } else {
        Write-Warning "JED not found for $Stem — check $fitLog"
        exit 1
    }
}

Build-OnePld "system_ctrl_cu"
Build-OnePld "system_ctrl_dp"
Write-Host "Dual CPLD JED build complete (program CU first in JTAG chain)."
