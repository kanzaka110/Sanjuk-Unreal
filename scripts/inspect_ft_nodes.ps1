$j = Get-Content 'C:\Dev\Sanjuk-Unreal\Saved\ABRR_now_text.json' -Raw | ConvertFrom-Json
$ft = $j.nodes | Where-Object { $_.class -eq 'K2Node_FormatText' }
foreach ($n in $ft) {
    Write-Host ('--- {0} ---' -f $n.id)
    Write-Host ('  pos: {0}' -f ($n.pos -join ','))
    $inputs = ($n.pins | Where-Object { $_.direction -eq 'input' }).Count
    $outputs = ($n.pins | Where-Object { $_.direction -eq 'output' }).Count
    Write-Host ('  pins: input={0} output={1}' -f $inputs, $outputs)
    $named = $n.pins | Where-Object { $_.name -ne 'Format' -and $_.name -ne 'Result' -and $_.direction -eq 'input' }
    Write-Host ('  arg pins: {0}' -f $named.Count)
    $hasConn = $named | Where-Object { $_.connected_to.Count -gt 0 }
    Write-Host ('  arg pins with wires: {0}' -f @($hasConn).Count)
}
