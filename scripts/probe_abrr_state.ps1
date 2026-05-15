# Phase 0 probe: check variables and AnimRewindRecorderEmit function existence
$varsFile  = 'C:\Dev\Sanjuk-Unreal\Saved\ABP_vars_text.json'
$funcsFile = 'C:\Dev\Sanjuk-Unreal\Saved\ABP_funcs_text.json'

$jv = Get-Content $varsFile  -Raw | ConvertFrom-Json
$jf = Get-Content $funcsFile -Raw | ConvertFrom-Json

$targets = @(
    'bIsSprintEndTransition',
    'RewindMonitorLine',
    'UpperBodyBlendWeight',
    'CurrentSequenceName',
    'TrjPastAngularVelocity',
    'TrjCurrentAngularVelocity',
    'bAnimRewindRecording'
)

Write-Host '--- VARIABLES ---'
foreach ($n in $targets) {
    $v = $jv.variables | Where-Object { $_.name -eq $n }
    if ($v) {
        $cat = if ($v.category) { $v.category } else { '<none>' }
        $ie  = if ($null -ne $v.is_instance_editable) { $v.is_instance_editable } else { '?' }
        Write-Host ("FOUND {0,-30} type={1,-30} cat={2,-15} IE={3}" -f $n, $v.type, $cat, $ie)
    } else {
        Write-Host ("MISSING {0}" -f $n)
    }
}

Write-Host ''
Write-Host '--- AnimRewindRecorderEmit FUNCTION ---'
$f = $jf.functions | Where-Object { $_.name -eq 'AnimRewindRecorderEmit' }
if ($f) {
    Write-Host 'AnimRewindRecorderEmit EXISTS'
    $f | ConvertTo-Json -Depth 5
} else {
    Write-Host 'AnimRewindRecorderEmit MISSING - needs creation'
}

Write-Host ''
Write-Host '--- UpdateValueFromPostEvaluation FUNCTION ---'
$f2 = $jf.functions | Where-Object { $_.name -eq 'UpdateValueFromPostEvaluation' }
if ($f2) {
    Write-Host 'UpdateValueFromPostEvaluation EXISTS'
    $f2 | ConvertTo-Json -Depth 5
} else {
    Write-Host 'UpdateValueFromPostEvaluation MISSING'
}
