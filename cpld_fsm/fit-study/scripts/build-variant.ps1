# Merge ctrl_lut.inc into variant PLD and optionally run WinCUPL.
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet(
        "a1_a2_a3",
        "d5a_eeprom",
        "e1_gpr_eeprom",
        "e1_gpr_eeprom_trim",
        "e1_gpr_eeprom_q14"
    )]
    [string]$Variant
)

$ErrorActionPreference = "Stop"
$VariantDir = Join-Path $PSScriptRoot "..\variants\$Variant"
$HdlDir = Join-Path $PSScriptRoot "..\..\hdl"
$BasePld = Join-Path $VariantDir "system_ctrl.pld"
$GenPld = Join-Path $VariantDir "system_ctrl_gen.pld"
$LutInc = Join-Path $HdlDir "ctrl_lut.inc"

if (-not (Test-Path $BasePld)) { throw "Missing $BasePld" }

$content = Get-Content $BasePld -Raw
if ($Variant -eq "a1_a2_a3") {
    if (-not (Test-Path $LutInc)) {
        Push-Location $HdlDir
        python gen_ctrl_lut.py
        Pop-Location
    }
    $lut = Get-Content $LutInc -Raw
    $content = $content -replace '(?s)/\* GEN_CTRL_LUT_BEGIN \*/.*?/\* GEN_CTRL_LUT_END \*/', "`n/* GEN_CTRL_LUT_BEGIN */`n$lut/* GEN_CTRL_LUT_END */"
}

Set-Content -Path $GenPld -Value $content -NoNewline
Write-Host "Wrote $GenPld"

$Repo = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
$Wincupl = $env:WINCUPL_DIR
foreach ($c in @("C:\WinCUPL", "C:\Wincupl", "C:\Program Files\WinCUPL")) {
    if (-not $Wincupl -and (Test-Path $c)) { $Wincupl = $c }
}

$LogDir = Join-Path $PSScriptRoot "..\fit-logs"
$LogStem = if ($Variant -like "e1_*") { $Variant } else { $Variant }
$LogFile = Join-Path $LogDir "$LogStem-synthesis.txt"

if (-not $Wincupl) {
    @(
        "WinCUPL not found — structural fork only.",
        "Variant: $Variant",
        "Generated: $GenPld",
        "Pin budget: see pin-budget-e1.md (E1) or pin-budget-variants.md",
        "Action: open system_ctrl_gen.pld in WinCUPL F9 locally"
    ) | Set-Content $LogFile
    Write-Host "Logged desk-check to $LogFile"
    exit 0
}

$Cupl = Join-Path $Wincupl "Shared\cupl.exe"
if (-not (Test-Path $Cupl)) {
    Write-Warning "cupl.exe not found under $Wincupl"
    exit 0
}

Push-Location $VariantDir
& $Cupl $GenPld
Pop-Location

@(
    "Variant: $Variant",
    "WinCUPL dir: $Wincupl",
    "Generated PLD: $GenPld",
    "Check fitter log in $VariantDir for 'Design fits'"
) | Set-Content $LogFile
Write-Host "Synthesis attempted — see $LogFile and $VariantDir\*.fit"
