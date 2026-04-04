# 🐊 Jacazul Bootstrap - GitHub Orientation (PowerShell)
# This script handles GitHub CLI check and guides the user through authentication.

Write-Host "==================================="
Write-Host "GitHub CLI Orientation"
Write-Host "==================================="

# 1. Check for gh CLI
$ghPath = Get-Command gh -ErrorAction SilentlyContinue
if (!$ghPath) {
    Write-Host "❌ ERROR: 'gh' (GitHub CLI) is not installed." -ForegroundColor Red
    Write-Host "   Action: Please install it using winget or download from github.com." -ForegroundColor Yellow
    Write-Host "   Command: winget install GitHub.cli" -ForegroundColor Yellow
    return
}

Write-Host "✅ GitHub CLI (gh) detected." -ForegroundColor Green

# 2. Check Authentication Status
Write-Host "🐊 Checking authentication status..." -ForegroundColor Cyan
& gh auth status

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ You are already logged into GitHub." -ForegroundColor Green
    Write-Host "   Jacazul can now use the Broker to manage your issues and PRs." -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "⚠️  You are NOT logged into GitHub CLI." -ForegroundColor Yellow
    Write-Host "   Action: Run the following command to authenticate:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   gh auth login" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "   Pro-tip: Choose 'GitHub.com', 'HTTPS', and 'Web browser' for the easiest flow." -ForegroundColor Gray
}

Write-Host ""
Write-Host "Need custom tokens for specific Orgs/Projects?"
Write-Host "Run 'jacazul-github --help' (Coming soon!)"
Write-Host "==================================="
