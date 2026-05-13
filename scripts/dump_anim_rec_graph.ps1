param([string]$Path)
$j = Get-Content -Raw $Path | ConvertFrom-Json
$text = $j.result.content[0].text | ConvertFrom-Json
Write-Host "=== Graph: $($text.graph_name) ==="
Write-Host "Node count: $($text.nodes.Count)"
Write-Host ""
foreach ($n in $text.nodes) {
    $name = $n.name
    $cls = $n.class_name
    $title = $n.title
    Write-Host "[$name] class=$cls title=$title"
    if ($n.pins) {
        foreach ($p in $n.pins) {
            $dir = $p.direction
            $pn = $p.name
            $pt = $p.pin_type
            $links = ""
            if ($p.linked_to) {
                $links = ($p.linked_to | ForEach-Object { "$($_.node_name).$($_.pin_name)" }) -join ", "
            }
            $def = $p.default_value
            Write-Host "  ($dir) $pn : $pt = $def -> [$links]"
        }
    }
    Write-Host ""
}
