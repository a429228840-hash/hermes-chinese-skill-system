<#
.SYNOPSIS
    Install Hermes Chinese Skill System plugin for Windows.

.DESCRIPTION
    Installs the cn-skill-loader plugin and chinese-skill-index.json into
    the Hermes profile directory. Checks config.yaml and prompts the user
    to enable the plugin if not already present.

.PARAMETER WhatIf
    Preview what the script would do without making any changes.

.PARAMETER Confirm
    Prompt for confirmation before each destructive operation.

.EXAMPLE
    .\install.ps1

.EXAMPLE
    .\install.ps1 -WhatIf

.EXAMPLE
    .\install.ps1 -Confirm
#>

[CmdletBinding(SupportsShouldProcess = $true)]
param()

#Requires -Version 5.1

# ── Colour helpers ──────────────────────────────────────────────────────────
$C_RESET   = @{ ForegroundColor = 'White' }
$C_INFO    = @{ ForegroundColor = 'Cyan' }
$C_OK      = @{ ForegroundColor = 'Green' }
$C_WARN    = @{ ForegroundColor = 'Yellow' }
$C_ERROR   = @{ ForegroundColor = 'Red' }
$C_HEADING = @{ ForegroundColor = 'Magenta' }

function Write-Info  { Write-Host "[INFO]  $($args[0])" @C_INFO }
function Write-Ok   { Write-Host "[OK]    $($args[0])" @C_OK }
function Write-Warn { Write-Host "[WARN]  $($args[0])" @C_WARN }
function Write-Err  { Write-Host "[ERROR] $($args[0])" @C_ERROR }
function Write-Step { Write-Host "`n──> $($args[0])" @C_HEADING }

# ── Admin elevation check ───────────────────────────────────────────────────
$isAdmin = [Security.Principal.WindowsPrincipal]::new(
    [Security.Principal.WindowsIdentity]::GetCurrent()
).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Warn "Not running as Administrator."
    Write-Warn "Some operations (e.g. symlinks under protected paths) may fail."
    Write-Warn "Consider re-running from an elevated PowerShell prompt."
}

# ── Determine paths ─────────────────────────────────────────────────────────
$ErrorActionPreference = 'Stop'

try {
    $repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
    Write-Info "Repository root: $repoRoot"
} catch {
    Write-Err "Could not resolve repository root from script path '$PSScriptRoot'."
    throw
}

# Source paths inside the repo
$pluginSrc  = Join-Path $repoRoot 'plugin' 'cn-skill-loader'
$skillSrc   = Join-Path $repoRoot 'skills' 'chinese-skill-index.json'

# Hermes profile directory
$hermesHome = if ($env:HERMES_HOME) {
    $env:HERMES_HOME
} else {
    Join-Path $HOME '.hermes'
}

Write-Info "Hermes home directory: $hermesHome"

# Destination paths
$pluginDest   = Join-Path $hermesHome 'plugins' 'cn-skill-loader'
$skillDest    = Join-Path $hermesHome 'skills'
$skillFile    = Join-Path $skillDest 'chinese-skill-index.json'
$configFile   = Join-Path $hermesHome 'config.yaml'

# ── Validate source paths ───────────────────────────────────────────────────
if (-not (Test-Path $pluginSrc)) {
    Write-Err "Plugin source directory not found: $pluginSrc"
    throw "Missing plugin directory"
}
if (-not (Test-Path $skillSrc)) {
    Write-Err "Skill index source not found: $skillSrc"
    throw "Missing skill index file"
}

# ── 1. Copy plugin ─────────────────────────────────────────────────────────
Write-Step "Step 1: Installing cn-skill-loader plugin"

if ($PSCmdlet.ShouldProcess($pluginDest, "Copy plugin directory from '$pluginSrc'")) {
    try {
        if (-not (Test-Path (Split-Path $pluginDest -Parent))) {
            New-Item -Path (Split-Path $pluginDest -Parent) -ItemType Directory -Force | Out-Null
            Write-Info "Created plugins directory: $(Split-Path $pluginDest -Parent)"
        }

        if (Test-Path $pluginDest) {
            Write-Warn "Plugin directory already exists: $pluginDest"
            $answer = if ($PSBoundParameters.ContainsKey('Confirm')) {
                'Y'
            } else {
                Read-Host "  Overwrite? [y/N]"
            }
            if ($answer -ne 'y' -and $answer -ne 'Y') {
                Write-Warn "Skipping plugin copy."
            } else {
                Remove-Item -Path $pluginDest -Recurse -Force
                Copy-Item -Path $pluginSrc -Destination $pluginDest -Recurse -Force
                Write-Ok "Plugin overwritten: $pluginDest"
            }
        } else {
            Copy-Item -Path $pluginSrc -Destination $pluginDest -Recurse -Force
            Write-Ok "Plugin installed: $pluginDest"
        }
    } catch {
        Write-Err "Failed to copy plugin: $($_.Exception.Message)"
        throw
    }
}

# ── 2. Copy skill index ───────────────────────────────────────────────────
Write-Step "Step 2: Copying skill index"

if ($PSCmdlet.ShouldProcess($skillFile, "Copy skill index from '$skillSrc'")) {
    try {
        if (-not (Test-Path $skillDest)) {
            New-Item -Path $skillDest -ItemType Directory -Force | Out-Null
            Write-Info "Created skills directory: $skillDest"
        }

        if (Test-Path $skillFile) {
            Write-Warn "Skill index already exists: $skillFile"
            $answer = if ($PSBoundParameters.ContainsKey('Confirm')) {
                'Y'
            } else {
                Read-Host "  Overwrite? [y/N]"
            }
            if ($answer -ne 'y' -and $answer -ne 'Y') {
                Write-Warn "Skipping skill index copy."
            } else {
                Remove-Item -Path $skillFile -Force
                Copy-Item -Path $skillSrc -Destination $skillFile -Force
                Write-Ok "Skill index overwritten: $skillFile"
            }
        } else {
            Copy-Item -Path $skillSrc -Destination $skillFile -Force
            Write-Ok "Skill index copied: $skillFile"
        }
    } catch {
        Write-Err "Failed to copy skill index: $($_.Exception.Message)"
        throw
    }
}

# ── 3. Check config.yaml ──────────────────────────────────────────────────
Write-Step "Step 3: Checking Hermes configuration"

if ($PSCmdlet.ShouldProcess($configFile, "Check and suggest enabling cn-skill-loader")) {
    try {
        if (Test-Path $configFile) {
            $configContent = Get-Content -Path $configFile -Raw -ErrorAction Stop

            if ($configContent -match 'cn-skill-loader') {
                Write-Ok "Plugin 'cn-skill-loader' is already referenced in config.yaml"
            } else {
                Write-Warn "Plugin 'cn-skill-loader' is NOT enabled in config.yaml."
                Write-Host ""
                Write-Host "  Add the following to $configFile" @C_WARN
                Write-Host ""
                Write-Host "    plugins:" @C_INFO
                Write-Host "      enabled:" @C_INFO
                Write-Host "        - cn-skill-loader" @C_INFO
                Write-Host ""

                $answer = Read-Host "  Would you like me to add it now? [y/N]"
                if ($answer -eq 'y' -or $answer -eq 'Y') {
                    # Append the config entry to config.yaml
                    Add-Content -Path $configFile -Value "`nplugins:" -NoNewLine
                    Add-Content -Path $configFile -Value "`n  enabled:" -NoNewLine
                    Add-Content -Path $configFile -Value "`n    - cn-skill-loader" -NoNewLine
                    Add-Content -Path $configFile -Value "`n"
                    Write-Ok "Plugin added to config.yaml"
                } else {
                    Write-Warn "Skipped. Add it manually before restarting Hermes."
                }
            }
        } else {
            Write-Warn "No config.yaml found at: $configFile"
            Write-Host ""
            Write-Host "  Create $configFile with the following content:" @C_WARN
            Write-Host ""
            Write-Host "    plugins:" @C_INFO
            Write-Host "      enabled:" @C_INFO
            Write-Host "        - cn-skill-loader" @C_INFO
            Write-Host "    profile:" @C_INFO
            Write-Host "      name: default" @C_INFO
            Write-Host ""

            $answer = Read-Host "  Would you like me to create it now? [y/N]"
            if ($answer -eq 'y' -or $answer -eq 'Y') {
                $content = @"
plugins:
  enabled:
    - cn-skill-loader
profile:
  name: default
"@
                Set-Content -Path $configFile -Value $content -Encoding UTF8
                Write-Ok "config.yaml created at: $configFile"
            } else {
                Write-Warn "Skipped. Create it manually before restarting Hermes."
            }
        }
    } catch {
        Write-Err "Failed to check/update config.yaml: $($_.Exception.Message)"
        throw
    }
}

# ── Summary ────────────────────────────────────────────────────────────────
Write-Step "Installation complete"
Write-Host ""
Write-Host "🎉 Hermes Chinese Skill System installed!" @C_OK
Write-Host ""
Write-Host "  Plugin:     $pluginDest" @C_INFO
Write-Host "  Skills:     $skillFile" @C_INFO
Write-Host "  Config:     $configFile" @C_INFO
Write-Host ""
Write-Host "  Next steps:" @C_HEADING
Write-Host "    1. Ensure 'cn-skill-loader' is listed under plugins.enabled in config.yaml" @C_INFO
Write-Host "    2. Restart your Hermes session to activate" @C_INFO
Write-Host "    3. After upgrading hermes-agent, run:" @C_INFO
Write-Host "       python $(Join-Path $repoRoot 'scripts' 'hermes-cn-patches.py')" @C_INFO
Write-Host ""
