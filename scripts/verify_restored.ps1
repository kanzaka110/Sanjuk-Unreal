$j = Get-Content 'C:\Dev\Sanjuk-Unreal\Saved\PROBE_AnimRewindRecorderEmit_restored_20260515.json' -Raw | ConvertFrom-Json
Write-Host ('Graph: {0}' -f $j.graph_name)
Write-Host ('Total nodes: {0}' -f $j.nodes.Count)
$cls = $j.nodes | Group-Object class | Sort-Object Count -Descending
$cls | Format-Table Count, Name -AutoSize

# Count edges via input pins with connected_to
$edges = 0
foreach ($n in $j.nodes) {
    foreach ($p in $n.pins) {
        if ($p.direction -eq 'input' -and $p.connected_to -and $p.connected_to.Count -gt 0) {
            $edges += $p.connected_to.Count
        }
    }
}
Write-Host ('Total input-side connections: {0}' -f $edges)

# Check FormatText
$ft = $j.nodes | Where-Object { $_.class -eq 'K2Node_FormatText' }
Write-Host ('FormatText count: {0}' -f @($ft).Count)
foreach ($f in $ft) {
    $inputArgs = $f.pins | Where-Object { $_.direction -eq 'input' -and $_.name -ne 'Format' }
    $wired = $inputArgs | Where-Object { $_.connected_to -and $_.connected_to.Count -gt 0 }
    Write-Host ('  {0}: {1} arg pins, {2} wired' -f $f.id, @($inputArgs).Count, @($wired).Count)
    # downstream
    $result = $f.pins | Where-Object { $_.name -eq 'Result' }
    Write-Host ('    Result -> {0}' -f ($result.connected_to -join ' | '))
}
