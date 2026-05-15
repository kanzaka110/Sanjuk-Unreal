$j = Get-Content 'C:\Dev\Sanjuk-Unreal\Saved\PROBE_AnimRewindRecorderEmit_restored_20260515.json' -Raw | ConvertFrom-Json
$ft = $j.nodes | Where-Object { $_.class -eq 'K2Node_FormatText' } | Select-Object -First 1
$inputArgs = $ft.pins | Where-Object { $_.direction -eq 'input' -and $_.name -ne 'Format' }
Write-Host '=== Unwired FT arg pins ==='
foreach ($p in $inputArgs) {
    if (-not $p.connected_to -or $p.connected_to.Count -eq 0) {
        $dv = if ($p.default_value) { $p.default_value } else { '<empty>' }
        Write-Host ('  {0,-10} type={1,-10} default={2}' -f $p.name, $p.type, $dv)
    }
}
