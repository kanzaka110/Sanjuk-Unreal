# Extract node list from before/after backups and compute the new nodes (debug additions)
function Get-GraphFromBackup {
    param([string]$Path)
    $raw = Get-Content $Path -Raw | ConvertFrom-Json
    $textBlob = $raw.result.content[0]
    # The content is "@{type=text; text=...}" – textBlob may already be a hashtable when Powershell parses it
    if ($textBlob -is [string]) {
        # extract between text= and trailing }
        $m = [regex]::Match($textBlob, 'text=(.+)\}\s*$', 'Singleline')
        if (-not $m.Success) { throw "Cannot extract text from: $Path" }
        $json = $m.Groups[1].Value
    } else {
        $json = $textBlob.text
    }
    return ($json | ConvertFrom-Json)
}

$before = Get-GraphFromBackup 'C:\Dev\Sanjuk-Unreal\Saved\updvar_before_debug.json'
$after  = Get-GraphFromBackup 'C:\Dev\Sanjuk-Unreal\Saved\updvar_after_debug.json'

Write-Host ("BEFORE nodes: {0}" -f $before.nodes.Count)
Write-Host ("AFTER  nodes: {0}" -f $after.nodes.Count)
Write-Host ("DIFF        : {0}" -f ($after.nodes.Count - $before.nodes.Count))

$beforeIds = @{}
foreach ($n in $before.nodes) { $beforeIds[$n.id] = $true }

Write-Host ''
Write-Host '=== Nodes added in AFTER (not in BEFORE) ==='
$added = @()
foreach ($n in $after.nodes) {
    if (-not $beforeIds.ContainsKey($n.id)) {
        $added += $n
        Write-Host ("  + {0}  [{1}]  title={2}" -f $n.id, $n.class, $n.title)
    }
}
Write-Host ("Added count: {0}" -f $added.Count)

Write-Host ''
Write-Host '=== Nodes removed in AFTER (in BEFORE but missing in AFTER) ==='
$afterIds = @{}
foreach ($n in $after.nodes) { $afterIds[$n.id] = $true }
$removed = @()
foreach ($n in $before.nodes) {
    if (-not $afterIds.ContainsKey($n.id)) {
        $removed += $n
        Write-Host ("  - {0}  [{1}]  title={2}" -f $n.id, $n.class, $n.title)
    }
}
Write-Host ("Removed count: {0}" -f $removed.Count)

# Save added node IDs for the rollback step
$added | ForEach-Object { $_.id } | Out-File -Encoding utf8 'C:\Dev\Sanjuk-Unreal\Saved\rollback_added_node_ids_updvar.txt'
Write-Host ''
Write-Host 'Saved added node IDs -> C:\Dev\Sanjuk-Unreal\Saved\rollback_added_node_ids_updvar.txt'
