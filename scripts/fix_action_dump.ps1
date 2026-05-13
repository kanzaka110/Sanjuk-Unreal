param([string]$Graph, [string]$OutFile)

$paramsObj = @{
    asset_path = "/Game/Sanjuk_Common/Game/Character/Player/PC_01/Anim/PC_01_ABP.PC_01_ABP"
    graph_name = $Graph
}

$body = @{
    jsonrpc = "2.0"
    id      = 1
    method  = "tools/call"
    params  = @{
        name      = "blueprint_query"
        arguments = @{
            action = "get_graph_data"
            params = $paramsObj
        }
    }
} | ConvertTo-Json -Depth 20 -Compress

$resp = Invoke-RestMethod -Uri "http://localhost:9316/mcp" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 120

$resp | ConvertTo-Json -Depth 40 | Out-File -Encoding utf8 $OutFile
if ($resp.result.isError) {
    Write-Host "[isError=TRUE]"
    Write-Host $resp.result.content[0].text.Substring(0, [Math]::Min(500, $resp.result.content[0].text.Length))
} else {
    Write-Host "[isError=FALSE]"
    # try to extract nodes count
    $txt = $resp.result.content[0].text
    $parsed = $txt | ConvertFrom-Json
    Write-Host ("graph={0}  nodes={1}" -f $parsed.graph_name, $parsed.nodes.Count)
}
