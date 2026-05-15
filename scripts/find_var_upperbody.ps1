$j = Get-Content 'C:\Dev\Sanjuk-Unreal\Saved\ABP_vars_text.json' -Raw | ConvertFrom-Json
$matches = $j.variables | Where-Object { $_.name -like '*pper*' }
$matches | Format-Table name, type, category, is_instance_editable -AutoSize
Write-Host ('Found {0} matches' -f @($matches).Count)
