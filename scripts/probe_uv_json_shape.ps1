$j = Get-Content 'C:\Dev\Sanjuk-Unreal\Saved\Logs\phase110\uv_post.json' -Raw | ConvertFrom-Json
$body = $j.result.content[0].text | ConvertFrom-Json

Write-Host "top-level keys:"
$body.PSObject.Properties.Name | ForEach-Object { Write-Host "  - $_" }

if ($body.graph_data) {
    Write-Host "`ngraph_data keys:"
    $body.graph_data.PSObject.Properties.Name | ForEach-Object { Write-Host "  - $_" }
}
if ($body.nodes) {
    Write-Host ("nodes count = {0}" -f $body.nodes.Count)
}
if ($body.edges) {
    Write-Host ("edges count = {0}" -f $body.edges.Count)
}

# raw preview
Write-Host "`nfirst 500 chars of body:"
($j.result.content[0].text).Substring(0, [Math]::Min(500, ($j.result.content[0].text).Length))
