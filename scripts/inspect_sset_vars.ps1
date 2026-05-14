$j = Get-Content C:/Dev/Sanjuk-Unreal/scripts/probe_vars.out.json -Raw | ConvertFrom-Json
$text = $j.result.content[0].text | ConvertFrom-Json
$text.variables | Where-Object { $_.name -match 'SprintEnd' } | ConvertTo-Json -Depth 10
