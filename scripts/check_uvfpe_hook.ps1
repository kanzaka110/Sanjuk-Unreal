$j = Get-Content 'C:\Dev\Sanjuk-Unreal\Saved\UVFPE_after_text.json' -Raw | ConvertFrom-Json
Write-Host ('Nodes: {0}' -f $j.nodes.Count)
foreach ($n in $j.nodes) {
    Write-Host ('  {0,-35} {1}' -f $n.id, $n.class)
    foreach ($p in $n.pins) {
        if ($p.connected_to -and $p.connected_to.Count -gt 0) {
            $dir = $p.direction
            $conn = ($p.connected_to -join ' | ')
            Write-Host ('     [{0,-6}] {1,-20} -> {2}' -f $dir, $p.name, $conn)
        }
    }
}
