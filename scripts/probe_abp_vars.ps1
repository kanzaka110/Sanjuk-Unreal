$j = Get-Content 'C:\Dev\Sanjuk-Unreal\Saved\Logs\phase110\abp_vars.json' -Raw | ConvertFrom-Json
$body = $j.result.content[0].text | ConvertFrom-Json

Write-Host ("variables.count = {0}" -f $body.variables.Count)

$body.variables | Where-Object { $_.name -match 'CurrentSequenceName|CurrAnimTag|CurrentAnimTags|SprintEnd|bIsSprint' } | ForEach-Object {
    "{0,-44} type={1,-25} cat={2,-30} default={3} IE={4}" -f $_.name, $_.type, $_.category, $_.default_value, $_.instance_editable
}

Write-Host "`n=== Variables matching Sequence/Anim name pattern ==="
$body.variables | Where-Object { $_.name -match 'Sequence|AnimTag' } | ForEach-Object {
    "{0,-44} type={1,-25} cat={2}" -f $_.name, $_.type, $_.category
}
