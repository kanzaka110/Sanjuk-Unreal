$files = @{
    'Set_75'  = 'C:/Dev/Sanjuk-Unreal/scripts/verify_set75_post.json'
    'CF_38 (Remain>0)' = 'C:/Dev/Sanjuk-Unreal/scripts/verify_cf38_post.json'
    'CF_40 (AND)' = 'C:/Dev/Sanjuk-Unreal/scripts/verify_cf40_post.json'
}
foreach ($k in $files.Keys) {
    $j = Get-Content $files[$k] -Raw | ConvertFrom-Json
    $node = $j.result.content[0].text | ConvertFrom-Json
    Write-Host "==== $k ($($node.id)) ===="
    foreach ($p in $node.pins) {
        if (-not $p.is_exec) {
            Write-Host ("  [{0}] {1} ({2}) connected_to=[{3}]" -f $p.direction, $p.name, $p.type, ($p.connected_to -join ', '))
        }
    }
}
