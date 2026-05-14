$files = @{
    'Get_TRD'      = 'C:/Dev/Sanjuk-Unreal/scripts/pin_get_trd.json'
    'Abs'          = 'C:/Dev/Sanjuk-Unreal/scripts/pin_abs.json'
    'Get_Thr'      = 'C:/Dev/Sanjuk-Unreal/scripts/pin_get_threshold.json'
    'Greater'      = 'C:/Dev/Sanjuk-Unreal/scripts/pin_greater.json'
    'AND'          = 'C:/Dev/Sanjuk-Unreal/scripts/pin_and.json'
}
foreach ($k in $files.Keys) {
    $j = Get-Content $files[$k] -Raw | ConvertFrom-Json
    $node = $j.result.content[0].text | ConvertFrom-Json
    Write-Host "==== $k ($($node.id), $($node.class), title='$($node.title)', fn='$($node.function)') ===="
    foreach ($p in $node.pins) {
        Write-Host ("  [{0}] {1} ({2}) connected_to={3}" -f $p.direction, $p.name, $p.type, ($p.connected_to -join ','))
    }
}
