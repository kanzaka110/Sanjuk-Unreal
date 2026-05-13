param([string]$Path, [string]$Pattern)
$j = Get-Content -Raw $Path | ConvertFrom-Json
$text = $j.result.content[0].text | ConvertFrom-Json
$text.variables | Where-Object { $_.name -match $Pattern } | Select-Object name, type, category | ConvertTo-Json -Depth 5
