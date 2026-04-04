# 🐊 Jacazul Language Bootstrap (PowerShell)
# Loads and injects Chat and Data idiom preferences.

$JACAZUL_DIR = "$env:USERPROFILE\.jacazul-ai"
$LANG_JSON = "$JACAZUL_DIR\language.json"

# Default values
$env:JACAZUL_CHAT_LANG = "pt-br"
$env:JACAZUL_DATA_LANG = "en"

if (Test-Path $LANG_JSON) {
    try {
        $langConfig = Get-Content -Path $LANG_JSON -Raw | ConvertFrom-Json
        if ($langConfig.chat) { $env:JACAZUL_CHAT_LANG = $langConfig.chat }
        if ($langConfig.data) { $env:JACAZUL_DATA_LANG = $langConfig.data }
    } catch {
        # Fallback to defaults if JSON is corrupted
    }
}

# Log status in DEBUG mode
if ($env:DEBUG) {
    Write-Host "🌐 Jacazul Language: Chat=$($env:JACAZUL_CHAT_LANG) | Data=$($env:JACAZUL_DATA_LANG)"
}
