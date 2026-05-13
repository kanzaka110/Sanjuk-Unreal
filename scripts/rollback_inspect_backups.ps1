$before = Get-Content 'C:\Dev\Sanjuk-Unreal\Saved\updvar_before_debug.json' -Raw | ConvertFrom-Json
$after  = Get-Content 'C:\Dev\Sanjuk-Unreal\Saved\updvar_after_debug.json'  -Raw | ConvertFrom-Json

Write-Host '=== BEFORE keys ==='
$before.PSObject.Properties.Name

Write-Host ''
Write-Host '=== AFTER keys ==='
$after.PSObject.Properties.Name

Write-Host ''
Write-Host '=== BEFORE sample top ==='
$before | ConvertTo-Json -Depth 2 | Select-Object -First 1 | Out-String | ForEach-Object { $_.Substring(0, [Math]::Min(2000, $_.Length)) }
