<#
.SYNOPSIS
  One-line installer for Project Forge v1.0.0 (Codex Plugin)

.DESCRIPTION
  Downloads the latest Project Forge release and installs it into your
  Codex plugin directory. No git, no Python, no manual steps required.

  After installation, restart Codex to see Project Forge in your plugin list.

.USAGE
  irm https://raw.githubusercontent.com/Haozhenyu123/project-forge/main/install/install-codex.ps1 | iex

  Or download and run locally:
  .\install-codex.ps1
#>

param(
    [string]$Version = "1.0.0",
    [string]$CodexHome = $null,
    [string]$AgentsHome = $null,
    [switch]$Force = $false
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# ---- resolve paths ----
if (-not $CodexHome) {
    $CodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
}
if (-not $AgentsHome) {
    $AgentsHome = if ($env:AGENTS_HOME) { $env:AGENTS_HOME } else { Join-Path $HOME ".agents" }
}

$PluginDir   = Join-Path $CodexHome "plugins" "project-forge"
$MarketFile  = Join-Path $AgentsHome "plugins" "marketplace.json"
$BackupDir   = Join-Path $CodexHome "plugins" ".project-forge-backups"
$RepoUrl     = "https://github.com/Haozhenyu123/project-forge"
$ReleaseUrl  = "$RepoUrl/releases/download/v$Version/project-forge-codex-$Version.zip"
$FallbackUrl = "$RepoUrl/archive/refs/tags/v$Version.zip"
$TempZip     = Join-Path $env:TEMP "project-forge-codex-$Version.zip"
$TempExtract = Join-Path $env:TEMP "project-forge-install-$Version"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Project Forge v$Version - Codex Plugin Installer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Codex home  : $CodexHome"
Write-Host "Plugin dir  : $PluginDir"
Write-Host "Marketplace : $MarketFile"
Write-Host ""

# ---- check for existing installation ----
if (Test-Path $PluginDir) {
    if (-not $Force) {
        $existing = try {
            $manifest = Get-Content (Join-Path $PluginDir ".codex-plugin" "plugin.json") -Raw | ConvertFrom-Json
            $manifest.version
        } catch { "unknown" }
        Write-Host "[!] Project Forge v$existing is already installed at:" -ForegroundColor Yellow
        Write-Host "    $PluginDir" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "    To reinstall or upgrade, run with -Force." -ForegroundColor Yellow
        Write-Host "    The installer will back up your existing installation first." -ForegroundColor Yellow
        exit 1
    }

    # Back up existing installation
    $stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmss.ffffffZ")
    $backupPath = Join-Path $BackupDir "${stamp}-reinstall"
    Write-Host "[*] Backing up existing installation to: $backupPath" -ForegroundColor Gray
    New-Item -ItemType Directory -Force -Path $backupPath | Out-Null
    Copy-Item -Recurse -Force $PluginDir (Join-Path $backupPath "plugin")
    if (Test-Path $MarketFile) {
        Copy-Item -Force $MarketFile (Join-Path $backupPath "marketplace.json")
    }
    Write-Host "[+] Backup complete" -ForegroundColor Green
}

# ---- download ----
Write-Host "[*] Downloading Project Forge v$Version..." -ForegroundColor Gray
try {
    Invoke-WebRequest -Uri $ReleaseUrl -OutFile $TempZip -UseBasicParsing
    Write-Host "[+] Downloaded from GitHub Releases" -ForegroundColor Green
} catch {
    Write-Host "[!] Release download failed, trying fallback..." -ForegroundColor Yellow
    try {
        Invoke-WebRequest -Uri $FallbackUrl -OutFile $TempZip -UseBasicParsing
        Write-Host "[+] Downloaded from GitHub archive (fallback)" -ForegroundColor Green
    } catch {
        Write-Host "[X] Download failed. Check your internet connection or try again later." -ForegroundColor Red
        Write-Host "    Release URL: $ReleaseUrl" -ForegroundColor Red
        exit 1
    }
}

# ---- extract ----
Write-Host "[*] Extracting..." -ForegroundColor Gray
if (Test-Path $TempExtract) { Remove-Item -Recurse -Force $TempExtract }
New-Item -ItemType Directory -Force -Path $TempExtract | Out-Null

try {
    Expand-Archive -Path $TempZip -DestinationPath $TempExtract -Force
    Write-Host "[+] Extracted to staging" -ForegroundColor Green
} catch {
    Write-Host "[X] Extraction failed. The downloaded archive may be corrupt." -ForegroundColor Red
    exit 1
}

# ---- locate the plugin root inside the extracted archive ----
# Release zip structure: project-forge-codex-1.0.0/.codex-plugin/plugin.json
# Fallback structure: project-forge-1.0.0/.codex-plugin/plugin.json
$pluginRoot = $null
$candidates = Get-ChildItem -Directory $TempExtract | Sort-Object Name
foreach ($candidate in $candidates) {
    if (Test-Path (Join-Path $candidate.FullName ".codex-plugin" "plugin.json")) {
        $pluginRoot = $candidate.FullName
        break
    }
}

if (-not $pluginRoot) {
    Write-Host "[X] Could not find .codex-plugin/plugin.json in the extracted archive." -ForegroundColor Red
    Write-Host "    Contents of $TempExtract :" -ForegroundColor Red
    Get-ChildItem $TempExtract -Depth 2 | ForEach-Object { Write-Host "    $($_.FullName)" }
    exit 1
}

Write-Host "[+] Found plugin root: $pluginRoot" -ForegroundColor Green

# ---- install ----
Write-Host "[*] Installing to $PluginDir..." -ForegroundColor Gray

if (Test-Path $PluginDir) {
    Remove-Item -Recurse -Force $PluginDir
}

$PluginDirParent = Split-Path $PluginDir -Parent
New-Item -ItemType Directory -Force -Path $PluginDirParent | Out-Null
Copy-Item -Recurse -Force $pluginRoot $PluginDir

Write-Host "[+] Plugin files installed" -ForegroundColor Green

# ---- register in marketplace ----
Write-Host "[*] Registering in Codex marketplace..." -ForegroundColor Gray

$marketData = if (Test-Path $MarketFile) {
    try { Get-Content $MarketFile -Raw | ConvertFrom-Json } catch { @{} }
} else {
    @{}
}

# Ensure marketplace has the right structure
if (-not $marketData.name) { $marketData | Add-Member -NotePropertyName "name" -NotePropertyValue "personal" -Force }
if (-not $marketData.PSObject.Properties["interface"]) {
    $iface = [PSCustomObject]@{ displayName = "Personal Plugins" }
    $marketData | Add-Member -NotePropertyName "interface" -NotePropertyValue $iface -Force
}
if (-not $marketData.plugins) {
    $marketData | Add-Member -NotePropertyName "plugins" -NotePropertyValue @() -Force
}

# Remove old entry if it exists
$newPlugins = @()
foreach ($p in $marketData.plugins) {
    if ($p.name -ne "project-forge") {
        $newPlugins += $p
    }
}

# Add new entry
$entry = [PSCustomObject]@{
    name    = "project-forge"
    path    = $PluginDir
    version = $Version
}
$newPlugins += $entry
$marketData.plugins = $newPlugins

# Write back
$marketDir = Split-Path $MarketFile -Parent
New-Item -ItemType Directory -Force -Path $marketDir | Out-Null
$marketData | ConvertTo-Json -Depth 4 | Set-Content -Path $MarketFile -Encoding utf8

Write-Host "[+] Marketplace registered" -ForegroundColor Green

# ---- verify ----
Write-Host "[*] Verifying installation..." -ForegroundColor Gray
$installedManifest = Join-Path $PluginDir ".codex-plugin" "plugin.json"
if (Test-Path $installedManifest) {
    $manifest = Get-Content $installedManifest -Raw | ConvertFrom-Json
    $skills = (Get-ChildItem (Join-Path $PluginDir "skills") -Directory).Count
    Write-Host "[+] Manifest version: $($manifest.version)" -ForegroundColor Green
    Write-Host "[+] Skills detected : $skills" -ForegroundColor Green
} else {
    Write-Host "[X] Verification failed: manifest not found" -ForegroundColor Red
    exit 1
}

# ---- cleanup ----
Write-Host "[*] Cleaning up temporary files..." -ForegroundColor Gray
Remove-Item -Force $TempZip -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force $TempExtract -ErrorAction SilentlyContinue

# ---- done ----
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Project Forge v$Version installed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Restart Codex to see Project Forge in your plugin list." -ForegroundColor Yellow
Write-Host ""
Write-Host "  Next steps:" -ForegroundColor Gray
Write-Host "    1. Close and reopen the Codex desktop app" -ForegroundColor Gray
Write-Host "    2. Go to Settings > Plugins" -ForegroundColor Gray
Write-Host "    3. Find Project Forge under 'Personal'" -ForegroundColor Gray
Write-Host "    4. Toggle it ON if it isn't already" -ForegroundColor Gray
Write-Host "    5. Start a new chat and say:" -ForegroundColor Gray
Write-Host '       "I want to build a medical consultation app"' -ForegroundColor Gray
Write-Host ""
