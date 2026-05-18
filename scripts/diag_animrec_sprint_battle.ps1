param(
  [string]$LogPath = 'E:\Perforce\SB2\Workspace\Internal\SB2\Saved\Logs\SB2.log'
)

$ErrorActionPreference = 'Stop'

$L = Get-Content -LiteralPath $LogPath -Encoding UTF8

# 1) ANIM_REC 전체 분포
$idx = New-Object System.Collections.Generic.List[int]
for ($i = 0; $i -lt $L.Count; $i++) {
  if ($L[$i] -match 'ANIM_REC') { $idx.Add($i) }
}
Write-Output "=== ANIM_REC stats ==="
Write-Output ("total lines: {0}" -f $idx.Count)
if ($idx.Count -gt 0) {
  Write-Output ("first idx : {0}" -f $idx[0])
  Write-Output ("last  idx : {0}" -f $idx[$idx.Count-1])
  $firstSample = $L[$idx[0]]
  $lastSample  = $L[$idx[$idx.Count-1]]
  Write-Output ("first ts  : " + ($firstSample.Substring(0, [Math]::Min(40, $firstSample.Length))))
  Write-Output ("last  ts  : " + ($lastSample.Substring(0, [Math]::Min(40, $lastSample.Length))))
}

# 2) seq 분포 (ANIM_REC만)
Write-Output ""
Write-Output "=== seq distribution in ANIM_REC ==="
$seqCounts = @{}
$total = 0
foreach ($line in $L) {
  if ($line -match 'ANIM_REC' -and $line -match '"seq"=([A-Za-z0-9_]*)') {
    $s = $matches[1]
    if ([string]::IsNullOrEmpty($s)) { $s = '<empty>' }
    if ($seqCounts.ContainsKey($s)) { $seqCounts[$s] += 1 } else { $seqCounts[$s] = 1 }
    $total++
  }
}
Write-Output ("ANIM_REC w/ seq match: {0}" -f $total)
$seqCounts.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 30 | ForEach-Object {
  '{0,8}  {1}' -f $_.Value, $_.Key
}

# 3) Sprint_to_Battle 등장 어디서 (전체 라인)
Write-Output ""
Write-Output "=== Sprint_to_Battle_Jog_B_Lfoot occurrences (line types) ==="
$btnCnt = @{}
foreach ($line in $L) {
  if ($line -match 'Sprint_to_Battle_Jog_B_Lfoot') {
    if ($line -match '^\[[^\]]+\]\[[^\]]+\](Log[A-Za-z]+):') {
      $cat = $matches[1]
    } elseif ($line -match '^\[[^\]]+\]\[[^\]]+\]([A-Za-z]+):') {
      $cat = $matches[1]
    } else {
      $cat = '<other>'
    }
    if ($btnCnt.ContainsKey($cat)) { $btnCnt[$cat] += 1 } else { $btnCnt[$cat] = 1 }
  }
}
$btnCnt.GetEnumerator() | Sort-Object Value -Descending | ForEach-Object {
  '{0,4}  {1}' -f $_.Value, $_.Key
}

# 4) ANIM_REC seq 중 "Sprint" 또는 "Battle" 포함
Write-Output ""
Write-Output "=== ANIM_REC seqs containing Sprint or Battle ==="
$seqCounts.GetEnumerator() | Where-Object { $_.Key -match 'Sprint|Battle' } | Sort-Object Value -Descending | ForEach-Object {
  '{0,8}  {1}' -f $_.Value, $_.Key
}

# 5) PIE 세션 범위 출력
Write-Output ""
Write-Output "=== PIE sessions (start / end) ==="
for ($i = 0; $i -lt $L.Count; $i++) {
  if ($L[$i] -match 'PIE: 에디터에서 플레이 총 시작 시간|BeginTearingDown for /Game/Art/TA/TestLevel/UEDPIE') {
    $t = ''
    if ($L[$i] -match '^\[([^\]]+)\]') { $t = $matches[1] }
    $kind = if ($L[$i] -match 'BeginTearingDown') { 'END  ' } else { 'START' }
    '{0,6}  {1}  line {2}' -f $kind, $t, ($i+1)
  }
}
