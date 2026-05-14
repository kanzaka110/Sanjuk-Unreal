param(
    [string]$Path = 'C:\Dev\Sanjuk-Unreal\Saved\Logs\phase110\uv_post.json'
)

$j = Get-Content $Path -Raw | ConvertFrom-Json
$body = $j.result.content[0].text | ConvertFrom-Json
$nodes = $body.nodes

Write-Host ("graph='{0}', nodes={1}" -f $body.graph_name, $nodes.Count)

function Show-Node($n) {
    $extra = ''
    if ($n.function_name) { $extra = "fn=$($n.function_name)" }
    elseif ($n.variable_name) { $extra = "var=$($n.variable_name)" }
    elseif ($n.title) { $extra = "title=$($n.title)" }
    "{0,-34} {1,-46} ({2,5},{3,5}) {4}" -f $n.id, $n.class, $n.pos[0], $n.pos[1], $extra
}

Write-Host "`n=== Phase 1.9 / 1.10 key nodes ==="
$keys = '^K2Node_(CallFunction_(35|36|37|38|40|42|43|44|45)|IfThenElse_0|EnumInequality_2|VariableGet_(57|58|59|60|61|62|63|64|66|67|68)|VariableSet_(73|74|75)|ExecutionSequence_(0|3))$'
$nodes | Where-Object { $_.id -match $keys } | Sort-Object id | ForEach-Object { Show-Node $_ }

# Build pin-id -> node.pin lookup
$pinById = @{}
foreach ($n in $nodes) {
    foreach ($p in $n.pins) {
        if ($p.id) { $pinById[$p.id] = "$($n.id).$($p.name)" }
    }
}

function Inflows($nodeId, $pinName) {
    $node = $nodes | Where-Object id -eq $nodeId | Select-Object -First 1
    if (-not $node) { return }
    $pin = $node.pins | Where-Object name -eq $pinName | Select-Object -First 1
    if (-not $pin) { return }
    # connected_to on input pins
    if ($pin.connected_to) {
        foreach ($c in $pin.connected_to) { "  IN  $c -> $nodeId.$pinName" }
    }
    # And scan all nodes whose output pin lists this nodeId.pinName as target
    foreach ($n2 in $nodes) {
        foreach ($p2 in $n2.pins) {
            if ($p2.direction -eq 'output' -and $p2.connected_to -contains "$nodeId.$pinName") {
                "  OUT $($n2.id).$($p2.name) -> $nodeId.$pinName"
            }
        }
    }
}

function Outflows($nodeId, $pinName) {
    $node = $nodes | Where-Object id -eq $nodeId | Select-Object -First 1
    if (-not $node) { return }
    $pin = $node.pins | Where-Object name -eq $pinName | Select-Object -First 1
    if (-not $pin) { return }
    if ($pin.connected_to) {
        foreach ($c in $pin.connected_to) { "  $nodeId.$pinName -> $c" }
    }
}

Write-Host "`n=== Inflows to IfThenElse_0.Condition ==="
Inflows 'K2Node_IfThenElse_0' 'Condition'

Write-Host "`n=== Inflows to VariableSet_75 (bIsSprintEndTransition) ==="
$set75 = $nodes | Where-Object id -eq 'K2Node_VariableSet_75' | Select-Object -First 1
if ($set75) {
    foreach ($p in $set75.pins) {
        if ($p.direction -eq 'input') {
            Write-Host ("-- pin: {0} (type={1})" -f $p.name, $p.type)
            Inflows 'K2Node_VariableSet_75' $p.name
        }
    }
}

Write-Host "`n=== Outflows from CallFunction_44 (OR_Phase, Phase 1.9 final OR) ==="
$cf44 = $nodes | Where-Object id -eq 'K2Node_CallFunction_44' | Select-Object -First 1
if ($cf44) {
    foreach ($p in $cf44.pins) {
        Write-Host ("-- pin: {0} dir={1}" -f $p.name, $p.direction)
        Outflows 'K2Node_CallFunction_44' $p.name
    }
}

Write-Host "`n=== Inflows to CallFunction_44 (OR inputs) ==="
$cf44.pins | Where-Object direction -eq 'input' | ForEach-Object {
    Write-Host ("-- pin: {0} (type={1})" -f $_.name, $_.type)
    Inflows 'K2Node_CallFunction_44' $_.name
}

Write-Host "`n=== CurrentSequenceName variable usage ==="
$nodes | Where-Object { $_.variable_name -eq 'CurrentSequenceName' } | ForEach-Object { Show-Node $_ }

Write-Host "`n=== CurrAnimTag variable usage ==="
$nodes | Where-Object { $_.variable_name -eq 'CurrAnimTag' } | ForEach-Object { Show-Node $_ }

Write-Host "`n=== KismetStringLibrary / KismetTextLibrary / FName call functions ==="
$nodes | Where-Object {
    $_.class -eq 'K2Node_CallFunction' -and (
        $_.function_name -match 'Contains|StartsWith|EndsWith|ToString|Conv_NameToString|Conv_StringToName'
    )
} | ForEach-Object { Show-Node $_ }

Write-Host "`n=== All VariableGet referencing CurrentSequenceName or seq-related names ==="
$nodes | Where-Object {
    $_.class -eq 'K2Node_VariableGet' -and $_.variable_name -match 'CurrentSequence|Sequence|Anim'
} | ForEach-Object { Show-Node $_ }

# Look at CF_45 to see Phase 1.10 wire state
Write-Host "`n=== Inflows / Outflows for CallFunction_45 (Phase 1.10 final AND) ==="
$cf45 = $nodes | Where-Object id -eq 'K2Node_CallFunction_45' | Select-Object -First 1
if ($cf45) {
    Show-Node $cf45
    foreach ($p in $cf45.pins) {
        Write-Host ("-- pin: {0} dir={1} type={2}" -f $p.name, $p.direction, $p.type)
        if ($p.direction -eq 'input') { Inflows 'K2Node_CallFunction_45' $p.name }
        else { Outflows 'K2Node_CallFunction_45' $p.name }
    }
}

Write-Host "`n=== EnumInequality_2 detail ==="
$ei2 = $nodes | Where-Object id -eq 'K2Node_EnumInequality_2' | Select-Object -First 1
if ($ei2) {
    Show-Node $ei2
    $ei2.pins | ForEach-Object {
        $def = if ($_.default_value) { "default=$($_.default_value)" } else { '' }
        "  pin {0} dir={1} type={2} {3}" -f $_.name, $_.direction, $_.type, $def
    }
}
