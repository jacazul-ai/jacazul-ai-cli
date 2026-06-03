# 🐊 Jacazul Bootstrap - GitHub Orientation (PowerShell)
# This script handles GitHub CLI check and guides the user through authentication.

$scriptDir = Split-Path $MyInvocation.MyCommand.Path -Parent
if (!$scriptDir) { $scriptDir = $PSScriptRoot }
$PROJECT_ROOT = (Resolve-Path (Join-Path $scriptDir "..\..\")).Path

Write-Output "==================================="
Write-Output "GitHub CLI Orientation"
Write-Output "==================================="

# 1. Check for gh CLI
if (!(Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Output "❌ ERROR: 'gh' (GitHub CLI) is not installed."
    Write-Output "   Action: Please install it using winget or Chocolatey."
    Write-Output "   Winget: winget install --id GitHub.cli"
    Write-Output "   Chocolatey: choco install gh"
    return
}

Write-Output "✅ GitHub CLI (gh) detected."

# 2. Check Authentication Status
Write-Output "🐊 Checking authentication status..."
$ghStatus = (gh auth status 2>&1) | Out-String

if ($LASTEXITCODE -eq 0 -or $ghStatus -match "Logged in to github.com") {
    Write-Output ""
    Write-Output "✅ You are already logged into GitHub."
    Write-Output "   Jacazul can now use the Broker to manage your issues and PRs."
} else {
    Write-Output ""
    Write-Output "⚠️  You are NOT logged into GitHub CLI."
    Write-Output "   Action: Run the following command to authenticate:"
    Write-Output ""
    Write-Output "   gh auth login"
    Write-Output ""
    Write-Output "   Pro-tip: Choose 'GitHub.com', 'HTTPS', and 'Web browser' for the easiest flow."
}

Write-Output ""
Write-Output "Need custom tokens for specific Orgs/Projects?"
Write-Output "Run 'jacazul-github --help' (Coming soon!)"
Write-Output "==================================="
