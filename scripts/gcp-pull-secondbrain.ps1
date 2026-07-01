<#
.SYNOPSIS
  GCP 중앙 AI Context Hub → 회사 로컬 미러 pull.

.DESCRIPTION
  GCP VM(sanjuk-project)의 /home/kanzaka110/.ai-context/ 아래
  second-brain/ 와 shared-context/ 를 로컬 C:\dev\Hermes-SecondBrain\ 로 내려받는다.
  전송은 gcloud compute scp(기존 gcp-*.cmd 와 동일한 인증) 사용 — SSH 키/시크릿 하드코딩 없음.

  결과 구조:
    C:\dev\Hermes-SecondBrain\second-brain\   (00~07, Rooms\, Reports\ ...)
    C:\dev\Hermes-SecondBrain\shared-context\ (current-*.md)
  → 이 구조가 있어야 회사 PC Claude Code "8번 지시문 블록"이 동작한다.

  기존 Hermes 스냅샷(루트의 00_INDEX.md, Areas\, Sources\ 등)은 건드리지 않는다.

.PARAMETER Mirror
  지정 시 robocopy /MIR 로 GCP에 없는 로컬 파일까지 삭제(정확한 거울).
  기본은 추가/덮어쓰기만(로컬 전용 파일 보존).

.PARAMETER DryRun
  실제 전송 없이 실행할 gcloud 명령만 출력.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\gcp-pull-secondbrain.ps1
  powershell -ExecutionPolicy Bypass -File scripts\gcp-pull-secondbrain.ps1 -Mirror
#>
[CmdletBinding()]
param(
  [string]$VM         = "sanjuk-project",
  [string]$Zone       = "us-central1-b",
  [string]$RemoteBase = "/home/kanzaka110/.ai-context",  # 절대경로: gcloud 로그인은 SHIFTUP 유저이나 이 폴더는 world-readable
  [string]$LocalRoot  = "C:\dev\Hermes-SecondBrain",
  [string[]]$Folders  = @("second-brain","shared-context"),
  [switch]$Mirror,
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Resolve-Gcloud {
  $c = Get-Command gcloud.cmd -ErrorAction SilentlyContinue
  if ($c) { return $c.Source }
  foreach ($p in @(
      "C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd",
      "C:\Program Files\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd",
      "$env:LOCALAPPDATA\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd")) {
    if (Test-Path $p) { return $p }
  }
  throw "gcloud CLI 를 찾을 수 없음. Google Cloud SDK 설치/PATH 확인 (gcloud init 선행)."
}

$gcloud = Resolve-Gcloud
Write-Host "gcloud : $gcloud"
Write-Host "source : ${VM}:$RemoteBase  (zone $Zone)"
Write-Host "target : $LocalRoot"
Write-Host ("mode   : {0}" -f ($(if ($Mirror) { "MIRROR(/MIR, 로컬전용 삭제)" } else { "MERGE(추가/덮어쓰기)" })))

# 매 실행 새로 비우는 staging 으로 받고, 검증 후 최종 미러로 반영
$stamp   = Get-Date -Format "yyyyMMdd_HHmmss"
$staging = Join-Path $env:TEMP "aicontext_pull_$stamp"

if ($DryRun) {
  Write-Host "`n[DryRun] 실행 예정 명령:"
  foreach ($f in $Folders) {
    Write-Host "  & `"$gcloud`" compute scp --recurse --zone=$Zone `"${VM}:$RemoteBase/$f`" `"$staging`""
  }
  Write-Host "  robocopy `"$staging\<folder>`" `"$LocalRoot\<folder>`" $(if($Mirror){'/MIR'}else{'/E'}) ..."
  return
}

New-Item -ItemType Directory -Force -Path $staging | Out-Null
$ok = $false
try {
  foreach ($f in $Folders) {
    Write-Host "`n==> scp pull: $f"
    & $gcloud compute scp --recurse --zone=$Zone "${VM}:$RemoteBase/$f" $staging
    if ($LASTEXITCODE -ne 0) { throw "scp 실패 (exit $LASTEXITCODE): $f — gcloud 인증/네트워크/원격경로 확인" }
  }

  New-Item -ItemType Directory -Force -Path $LocalRoot | Out-Null
  # /E=하위 포함, /PURGE(-Mirror)=dst 전용파일 삭제. 긴 경로/재실행 nesting 방지 위해 robocopy 사용.
  $rcFlags = @("/E","/NFL","/NDL","/NP","/NJH","/NJS","/R:1","/W:2")
  if ($Mirror) { $rcFlags += "/PURGE" }

  foreach ($f in $Folders) {
    $src = Join-Path $staging $f
    $dst = Join-Path $LocalRoot $f
    if (-not (Test-Path $src)) {
      Write-Warning "staging 에 '$f' 없음 — scp 결과 구조 확인:"
      Get-ChildItem $staging -Force | Select-Object -First 20 | ForEach-Object { Write-Host "    $($_.Name)" }
      throw "'$f' 소스 폴더 없음"
    }
    Write-Host "`n==> robocopy: $f -> $dst"
    $rcOut = & robocopy $src $dst @rcFlags 2>&1
    $rc = $LASTEXITCODE
    # robocopy exit: 0~7 성공(비트플래그), 8+ 실패
    if ($rc -ge 8) {
      Write-Warning "robocopy exit $rc — 출력:"
      $rcOut | Select-Object -Last 15 | ForEach-Object { Write-Host "    $_" }
      throw "robocopy 실패 (exit $rc): $f"
    }
    $n = (Get-ChildItem $dst -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
    Write-Host "    파일 $n 개 (robocopy rc=$rc)"
  }
  Write-Host "`n완료 → $LocalRoot\{$($Folders -join ',')}"
  $ok = $true
}
finally {
  if ($ok) {
    if (Test-Path $staging) { Remove-Item -Recurse -Force $staging -ErrorAction SilentlyContinue }
  } else {
    Write-Warning "실패 — staging 보존(진단용): $staging"
  }
}
