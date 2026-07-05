# Pre-flash Tier 0-2 gate — no JTAG burn (local Windows + Python).
# Order: codegen -> pytest -> CUPL/fit -> .sim parity -> csim LUT

param(
    [switch]$SkipCsim
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Repo = Resolve-Path (Join-Path $Root "..\..")

Write-Host "=== Tier 0: codegen + pytest ==="
python (Join-Path $Root "gen_ctrl_lut.py")
python (Join-Path $Root "gen_csim_si.py")
Push-Location $Repo
python -m pytest cpld_fsm/hdl/tests simulators/cyclesim/tests -q
if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }
Pop-Location

Write-Host ""
Write-Host "=== Tier 0: CUPL compile + fit (JED, no burn) ==="
& (Join-Path $Root "build-wincupl.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "=== Tier 1a: .sim vs golden ==="
Push-Location $Repo
python -m pytest cpld_fsm/hdl/tests/test_sim_vs_golden.py -q
if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }
Pop-Location

if (-not $SkipCsim) {
    Write-Host ""
    Write-Host "=== Tier 1b: csim LUT-only ==="
    & (Join-Path $Root "run_csim_lut.ps1")
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} else {
    Write-Host ""
    Write-Host "Skipping csim (-SkipCsim)"
}

Write-Host ""
Write-Host "OK: pre-flash Tier 0-2 passed (no silicon burn)"
Write-Host "Next: M2a bench smoke after JTAG program of system_ctrl.jed"
