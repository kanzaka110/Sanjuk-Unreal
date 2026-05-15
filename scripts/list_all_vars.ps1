$j = Get-Content 'C:\Dev\Sanjuk-Unreal\Saved\ABP_vars_text.json' -Raw | ConvertFrom-Json
Write-Host ('Total variables: {0}' -f $j.variables.Count)
$j.variables | Where-Object { $_.name -like '*Body*' } | Format-Table name, type, category -AutoSize
Write-Host '---'
$j.variables | Where-Object { $_.type -eq 'float' } | Format-Table name, type, category -AutoSize
Write-Host '---'
$j.variables[0..3] | Format-Table name, type, category -AutoSize
