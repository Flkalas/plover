# WinCUPL csim on combinational ctrl_lut_csim (LUT-only, no fitter).
# Requires: cpld_fsm/tools/wincupl-ii (install-wincupl.ps1)

param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Repo = Resolve-Path (Join-Path $Root "..\..")
$Pld = Join-Path $Root "ctrl_lut_csim.pld"
$So = Join-Path $Root "ctrl_lut_csim.so"

Write-Host "Codegen ctrl_lut_csim ..."
python (Join-Path $Root "gen_ctrl_lut_csim.py")
if (-not (Test-Path $Pld)) {
    Write-Error "ctrl_lut_csim.pld not found after codegen"
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
    Write-Error "WinCUPL not found — run cpld_fsm/tools/install-wincupl.ps1"
}

$Cupl = Join-Path $Wincupl "Shared\cupl.exe"
$CuplDl = Join-Path $Wincupl "Shared\cupl.dl"
if (-not (Test-Path $Cupl)) {
    Write-Error "Missing $Cupl"
}

Write-Host "CUPL csim $Pld ..."
& $Cupl -s -n -a -l -e -x -m1 -u $CuplDl F1504ISPPLCC44 $Pld
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

if (-not (Test-Path $So)) {
    Write-Error "Missing $So after csim"
}

$soText = Get-Content $So -Raw -Encoding Byte
$text = [System.Text.Encoding]::GetEncoding(28591).GetString($soText)
$errs = [regex]::Matches($text, '\[\d{4}sa\]')
if ($errs.Count -gt 0) {
    Write-Host ""
    Write-Host "csim FAILED ($($errs.Count) error lines)"
    Select-String -Path $So -Pattern '\[\d{4}sa\]' | Select-Object -First 10 | ForEach-Object { Write-Host $_.Line }
    exit 1
}

Write-Host "OK: csim LUT vectors passed ($So)"
