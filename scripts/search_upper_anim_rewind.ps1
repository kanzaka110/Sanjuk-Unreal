$j = Get-Content 'C:\Dev\Sanjuk-Unreal\Saved\ABP_vars_text.json' -Raw | ConvertFrom-Json
Write-Host ('Total: {0}' -f $j.variables.Count)
Write-Host '--- Names containing Upper ---'
$j.variables | Where-Object { $_.name -match 'Upper' } | Format-Table name,type,category -AutoSize
Write-Host '--- AnimRewind category ---'
$j.variables | Where-Object { $_.category -eq 'AnimRewind' } | Format-Table name,type,category -AutoSize
Write-Host '--- Last 8 by name (alpha) ---'
$j.variables | Sort-Object name | Select-Object -Last 8 | Format-Table name,type,category -AutoSize
