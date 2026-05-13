# Generic Monolith MCP HTTP caller
param(
    [Parameter(Mandatory=$true)][string]$Tool,
    [Parameter(Mandatory=$true)][string]$Action,
    [Parameter(Mandatory=$true)][string]$ParamsJson,
    [string]$OutFile = $null,
    [int]$Id = 1
)

$body = @{
    jsonrpc = "2.0"
    id      = $Id
    method  = "tools/call"
    params  = @{
        name      = $Tool
        arguments = @{
            action = $Action
            params = ($ParamsJson | ConvertFrom-Json)
        }
    }
} | ConvertTo-Json -Depth 20 -Compress

if ($OutFile) {
    $resp = Invoke-RestMethod -Uri "http://localhost:9316/mcp" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 90
    $resp | ConvertTo-Json -Depth 30 | Out-File -Encoding utf8 $OutFile
    Write-Host ("Saved -> {0}" -f $OutFile)
} else {
    $resp = Invoke-RestMethod -Uri "http://localhost:9316/mcp" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 90
    $resp | ConvertTo-Json -Depth 30
}
