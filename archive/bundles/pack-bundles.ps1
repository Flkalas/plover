# Pack all code trees into archive/bundles/*.tar.gz (one-time before doc-only active tree).
# Run from repository root: powershell -File scripts/pack-bundles.ps1

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$OutDir = Join-Path $Root "archive\bundles"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$Commit = ""
try { $Commit = (git -C $Root rev-parse --short HEAD 2>$null) } catch {}
$Date = Get-Date -Format "yyyy-MM-dd"

$Bundles = @(
    @{ Name = "hwsim"; Paths = @("hwsim") },
    @{ Name = "cyclesim"; Paths = @("cyclesim") },
    @{ Name = "plover_vm"; Paths = @("plover_vm") },
    @{ Name = "rust_vm"; Paths = @("crates", "Cargo.toml", "Cargo.lock") },
    @{ Name = "tools"; Paths = @("tools") },
    @{ Name = "hw"; Paths = @("hw") },
    @{ Name = "tests_py"; Paths = @("tests") },
    @{ Name = "host_toolchain"; Paths = @("plover_asm", "plover_cc", "plover_ld", "forth", "kern") },
    @{ Name = "verilog_sim"; Paths = @("archive/verilog-sim") }
)

$ManifestLines = New-Object System.Collections.Generic.List[string]
$null = $ManifestLines.Add("# Archive bundles")
$null = $ManifestLines.Add("")
$null = $ManifestLines.Add("**Frozen:** $Date")
$null = $ManifestLines.Add("**Git commit:** $Commit")
$null = $ManifestLines.Add("")
$null = $ManifestLines.Add("Active repository is Markdown-only for breadboard truth.")
$null = $ManifestLines.Add("Restore: tar -xzf archive/bundles/NAME.tar.gz -C .")
$null = $ManifestLines.Add("")
$null = $ManifestLines.Add("See docs/developer/archived-code-guide.md.")
$null = $ManifestLines.Add("")
$null = $ManifestLines.Add("| Bundle | Contents |")
$null = $ManifestLines.Add("|--------|----------|")

foreach ($b in $Bundles) {
    $name = $b.Name
    $tarName = "$name.tar.gz"
    $tarPath = Join-Path $OutDir $tarName
    $existing = New-Object System.Collections.Generic.List[string]
    foreach ($p in $b.Paths) {
        $full = Join-Path $Root $p
        if (Test-Path $full) {
            $null = $existing.Add($p)
        } else {
            Write-Warning "skip missing: $p"
        }
    }
    if ($existing.Count -eq 0) {
        Write-Warning "no paths for bundle $name"
        continue
    }
    if (Test-Path $tarPath) { Remove-Item $tarPath -Force }
    Push-Location $Root
    try {
        if ($name -eq "verilog_sim") {
            & tar -czf $tarPath --exclude=node_modules archive/verilog-sim
        } else {
            $args = @("-czf", $tarPath) + [string[]]$existing
            & tar @args
        }
        if ($LASTEXITCODE -ne 0) { throw "tar failed for $name" }
    } finally { Pop-Location }
    $sizeKb = [math]::Round((Get-Item $tarPath).Length / 1024)
    Write-Host "wrote $tarPath ($sizeKb KiB)"
    $null = $ManifestLines.Add("| $tarName | $($existing -join ', ') |")
    $readmeDir = Join-Path $OutDir $name
    New-Item -ItemType Directory -Force -Path $readmeDir | Out-Null
    $readme = @(
        "# $name",
        "",
        "Frozen: $Date - commit $Commit",
        "",
        "Not used for v1.0 breadboard SoC decisions. See archived-code-guide.",
        "",
        "Legacy concepts: alu8_decode, Flash CW at 0x4000, cpu_cw_direct, pareto search.",
        "",
        "Restore: tar -xzf archive/bundles/$tarName -C /path/to/plover"
    ) -join [Environment]::NewLine
    [System.IO.File]::WriteAllText((Join-Path $readmeDir "README.md"), $readme)
}

$null = $ManifestLines.Add("")
$null = $ManifestLines.Add("## Not bundled")
$null = $ManifestLines.Add("")
$null = $ManifestLines.Add("- build/ - gitignored sim artifacts")
$null = $ManifestLines.Add("- docs/ - remains active")
$null = $ManifestLines.Add("- hw-sim / rust-vm CI workflows removed")

[System.IO.File]::WriteAllText((Join-Path $OutDir "MANIFEST.md"), ($ManifestLines -join [Environment]::NewLine))
Write-Host "done -> $OutDir"
