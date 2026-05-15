# Search available blueprint_query actions for keywords
$body = @{
    jsonrpc = "2.0"
    id = 1
    method = "tools/list"
} | ConvertTo-Json -Compress

$resp = Invoke-RestMethod -Uri "http://localhost:9316/mcp" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 30
$bp = $resp.result.tools | Where-Object { $_.name -eq 'blueprint_query' }
$actions = $bp.inputSchema.properties.action.enum
Write-Host ('Total blueprint_query actions: {0}' -f $actions.Count)
Write-Host '--- Actions matching split/struct/pin ---'
$actions | Where-Object { $_ -match 'split|struct|pin' }
Write-Host ''
Write-Host '--- Actions matching enum ---'
$actions | Where-Object { $_ -match 'enum' }
