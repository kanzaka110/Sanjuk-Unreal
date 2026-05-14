$j = Get-Content 'C:\Dev\Sanjuk-Unreal\Saved\Logs\phase110\uv_post.json' -Raw | ConvertFrom-Json
$body = $j.result.content[0].text | ConvertFrom-Json
$nodes = $body.nodes

Write-Host "=== Highest existing IDs by class ==="
$classes = 'K2Node_VariableGet', 'K2Node_VariableSet', 'K2Node_CallFunction', 'K2Node_FormatText', 'K2Node_IfThenElse', 'K2Node_EnumInequality', 'K2Node_EnumEquality'
foreach ($cls in $classes) {
    $maxId = -1
    $maxName = ''
    foreach ($n in $nodes) {
        if ($n.class -eq $cls) {
            if ($n.id -match '_(\d+)$') {
                $num = [int]$matches[1]
                if ($num -gt $maxId) { $maxId = $num; $maxName = $n.id }
            }
        }
    }
    "{0,-32} max id={1,-4} ({2})" -f $cls, $maxId, $maxName
}

Write-Host "`n=== ANIM_REC seq pin source (looking for CurrentSequenceName Get in AnimRewindRecorderEmit) ==="
$nodes | Where-Object { $_.variable_name -match 'CurrentSequence' } | ForEach-Object { "$($_.id) class=$($_.class) var=$($_.variable_name) pos=$($_.pos[0]),$($_.pos[1])" }
