<#
.SYNOPSIS
  Claude Code 트랜스크립트 자동삭제 기간(cleanupPeriodDays)을 안전하게 변경한다.

.DESCRIPTION
  회사 PC에서 실행. %USERPROFILE%\.claude\settings.json (또는 $env:CLAUDE_CONFIG_DIR\settings.json)
  의 다른 설정은 그대로 두고 cleanupPeriodDays 값만 바꾼다. 변경 전 타임스탬프 백업을 뜬다.
  기본값 3650일(약 10년) = 사실상 자동삭제 비활성.

  주의: 이미 삭제된 과거 세션은 이 스크립트로 복구되지 않는다. 앞으로 삭제를 막는 용도다.

.PARAMETER Days
  설정할 보존 일수. 기본 3650.

.PARAMETER ConfigDir
  .claude 설정 폴더 경로. 미지정 시 $env:CLAUDE_CONFIG_DIR → %USERPROFILE%\.claude 순.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\set_cleanup_period.ps1
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\set_cleanup_period.ps1 -Days 5000
#>
[CmdletBinding()]
param(
    [int]$Days = 3650,
    [string]$ConfigDir
)

$ErrorActionPreference = 'Stop'

# 1) 설정 폴더/파일 경로 결정
if (-not $ConfigDir) {
    if ($env:CLAUDE_CONFIG_DIR) { $ConfigDir = $env:CLAUDE_CONFIG_DIR }
    else { $ConfigDir = Join-Path $env:USERPROFILE '.claude' }
}
$settingsPath = Join-Path $ConfigDir 'settings.json'
Write-Host "설정 파일: $settingsPath"

# 2) 기존 설정 로드 (없으면 빈 객체)
if (Test-Path $settingsPath) {
    $rawText = Get-Content $settingsPath -Raw -Encoding UTF8
    if ([string]::IsNullOrWhiteSpace($rawText)) {
        $settings = [ordered]@{}
    } else {
        try {
            $settings = $rawText | ConvertFrom-Json
        } catch {
            throw "settings.json 파싱 실패 — 손상됐을 수 있음. 수동 확인 필요: $($_.Exception.Message)"
        }
    }

    # 3) 변경 전 백업 (한 번만, 타임스탬프)
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $backupPath = "$settingsPath.bak-$stamp"
    Copy-Item $settingsPath $backupPath -Force
    Write-Host "백업 생성: $backupPath"
} else {
    Write-Host "settings.json 없음 → 새로 생성한다."
    if (-not (Test-Path $ConfigDir)) { New-Item -ItemType Directory -Path $ConfigDir -Force | Out-Null }
    $settings = [ordered]@{}
}

# 4) 현재값 표시 → 변경
$before = $null
if ($settings.PSObject.Properties.Name -contains 'cleanupPeriodDays') {
    $before = $settings.cleanupPeriodDays
}
Write-Host ("현재 cleanupPeriodDays: {0}" -f ($(if ($null -ne $before) { $before } else { '(미설정 = 기본 30일)' })))

if ($settings -is [System.Collections.IDictionary]) {
    $settings['cleanupPeriodDays'] = $Days
} else {
    # ConvertFrom-Json 은 PSCustomObject → 속성 추가/갱신
    if ($settings.PSObject.Properties.Name -contains 'cleanupPeriodDays') {
        $settings.cleanupPeriodDays = $Days
    } else {
        $settings | Add-Member -NotePropertyName 'cleanupPeriodDays' -NotePropertyValue $Days -Force
    }
}

# 5) 저장 (Depth 크게 — 중첩 설정 잘림 방지). BOM 없는 UTF-8.
$json = $settings | ConvertTo-Json -Depth 100
[System.IO.File]::WriteAllText($settingsPath, $json, (New-Object System.Text.UTF8Encoding($false)))

# 6) 검증: 다시 읽어 확인
$verify = (Get-Content $settingsPath -Raw -Encoding UTF8 | ConvertFrom-Json).cleanupPeriodDays
if ($verify -eq $Days) {
    Write-Host ("완료 ✅  cleanupPeriodDays = {0} (약 {1:N1}년)" -f $verify, ($verify/365)) -ForegroundColor Green
    Write-Host "이제 오래된 세션이 자동삭제되지 않는다. (이미 삭제된 과거분은 복구 안 됨)"
} else {
    throw "검증 실패 — 기대 $Days, 실제 $verify"
}
