$j = Get-Content 'C:\Dev\Sanjuk-Unreal\Saved\ABRR_now_text.json' -Raw | ConvertFrom-Json
$nodes = $j.nodes
Write-Host ('Total nodes: {0}' -f $nodes.Count)
$counts = $nodes | Group-Object -Property class | Sort-Object Count -Descending
$counts | Format-Table Count, Name -AutoSize
Write-Host '--- FormatText nodes ---'
$nodes | Where-Object { $_.class -eq 'K2Node_FormatText' } | ForEach-Object { Write-Host ('  {0} at {1}' -f $_.id, ($_.pos -join ',')) }
Write-Host '--- FunctionEntry nodes ---'
$nodes | Where-Object { $_.class -eq 'K2Node_FunctionEntry' } | ForEach-Object { Write-Host ('  {0} at {1}' -f $_.id, ($_.pos -join ',')) }
