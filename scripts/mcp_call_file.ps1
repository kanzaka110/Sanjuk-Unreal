# Generic Monolith MCP HTTP caller — params loaded from a JSON file (avoids bash escaping)
param(
    [Parameter(Mandatory=$true)][string]$Tool,
    [Parameter(Mandatory=$true)][string]$Action,
    [Parameter(Mandatory=$true)][string]$ParamsFile,
    [string]$OutFile = $null,
    [int]$Id = 1
)

if (-not (Test-Path $ParamsFile)) {
    throw "ParamsFile not found: $ParamsFile"
}

$paramsObj = Get-Content $ParamsFile -Raw | ConvertFrom-Json

$body = @{
    jsonrpc = "2.0"
    id      = $Id
    method  = "tools/call"
    params  = @{
        name      = $Tool
        arguments = @{
            action = $Action
            params = $paramsObj
        }
    }
} | ConvertTo-Json -Depth 30 -Compress

try {
    $resp = Invoke-RestMethod -Uri "http://localhost:9316/mcp" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 120
} catch {
    Write-Host "HTTP error: $_"
    throw
}

if ($OutFile) {
    $resp | ConvertTo-Json -Depth 40 | Out-File -Encoding utf8 $OutFile
    Write-Host ("Saved -> {0}" -f $OutFile)

    # Quick status line
    if ($resp.result.isError) {
        Write-Host "[isError=TRUE]"
    } else {
        Write-Host "[isError=FALSE]"
    }
} else {
    $resp | ConvertTo-Json -Depth 40
}
