param([string]$Path)
$j = Get-Content -Raw $Path | ConvertFrom-Json
Write-Host ("NodeCount=" + $j.nodes.Count)
$ids = @('K2Node_FormatText_0','K2Node_VariableGet_0','K2Node_VariableGet_15','K2Node_VariableGet_21','K2Node_VariableGet_27','K2Node_CallFunction_0','K2Node_CallFunction_1','K2Node_FormatText_2','K2Node_FormatText_5')
foreach ($n in $j.nodes) {
    if ($ids -contains $n.id) {
        Write-Host ("--- " + $n.id + " (" + $n.title + ") ---")
        foreach ($p in $n.pins) {
            $links = ($p.connected_to -join ', ')
            Write-Host ("  " + $p.direction + " " + $p.name + " [" + $p.type + "] -> " + $links)
        }
    }
}
