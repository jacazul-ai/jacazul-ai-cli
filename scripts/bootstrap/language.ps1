# [Jacazul] Language Bootstrap (PowerShell Version)

$LANG_JSON = Join-Path $env:USERPROFILE ".jacazul-ai\language.json"

# Default values
$env:JACAZUL_CHAT_LANG = "pt-br"
$env:JACAZUL_DATA_LANG = "en"

if (Test-Path $LANG_JSON) {
    try {
        $langObj = Get-Content -Raw -Path $LANG_JSON | ConvertFrom-Json
        if ($langObj.chat) { $env:JACAZUL_CHAT_LANG = $langObj.chat }
        if ($langObj.data) { $env:JACAZUL_DATA_LANG = $langObj.data }
    } catch {
        # Silent fallback
    }
}

if ($env:DEBUG) {
    Write-Output "[INFO] Jacazul Language: Chat=$env:JACAZUL_CHAT_LANG | Data=$env:JACAZUL_DATA_LANG"
}