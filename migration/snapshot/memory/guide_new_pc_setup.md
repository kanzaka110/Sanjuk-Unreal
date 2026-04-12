---
name: 신규 PC 셋팅 가이드
description: 새 컴퓨터에서 Sanjuk-Unreal + Monolith + UnrealClaude + Claude Code 환경 구축 전체 절차
type: reference
---

# 신규 PC 셋팅 가이드

> 새 컴퓨터에서 Claude Code + UE5 + Monolith + UnrealClaude 작업 환경을 처음부터 구축하는 전체 절차.
> 회사 Perforce에 Monolith가 올라가지 않도록 로컬 전용으로 설치한다.
> (2026-04-06 최신화 — UnrealClaude 추가)

---

## 1단계: 기본 도구 설치

### 1-1. Git
- https://git-scm.com 에서 설치
- 설치 후 사용자 설정:
  ```bash
  git config --global user.name "kanzaka110"
  git config --global user.email "<이메일>"
  ```

### 1-2. Node.js (LTS)
- https://nodejs.org 에서 LTS 버전 설치
- runreal/unreal-mcp, UnrealClaude MCP 브릿지 실행에 필수

### 1-3. .NET Framework 4.8.1 Developer Pack
- UnrealClaude 플러그인 빌드에 필요
  ```bash
  winget install Microsoft.DotNet.Framework.DeveloperPack_4
  ```

### 1-4. Claude Code
- npm으로 설치:
  ```bash
  npm install -g @anthropic-ai/claude-code
  ```
- 또는 공식 데스크톱 앱 설치

---

## 2단계: UE5 에디터 설치

### 2-1. Epic Games Launcher에서 UE 5.7 설치
- Monolith, UnrealClaude 모두 UE 5.7 필요
- 설치 경로 예시: `C:\Program Files\Epic Games\UE_5.7\`

### 2-2. UE5 프로젝트 생성 또는 복사
- 테스트용 프로젝트 경로 예시: `C:\Users\<유저>\OneDrive\문서\Unreal Projects\MonolithTest`

---

## 3단계: Monolith 플러그인 설치 (로컬 전용, P4 미포함)

> **핵심 원칙**: 프로젝트 Plugins/ 폴더가 아닌, 엔진 레벨 또는 독립 경로에 설치하여 P4에 흔적을 남기지 않는다.

### 방법 A: 엔진 Plugins 폴더에 설치 (추천)

```
C:\Program Files\Epic Games\UE_5.7\Engine\Plugins\Marketplace\Monolith\
```

### 방법 B: 독립 경로 + 환경변수

```
변수명: UE_ADDITIONAL_PLUGIN_DIRS
값:     C:\MyLocalPlugins
```

### 설치 확인
- UE 에디터를 열면 Monolith MCP 서버가 `localhost:9316`에서 자동 실행됨

---

## 4단계: UnrealClaude 플러그인 설치

### 4-1. 소스 클론 및 빌드
```bash
cd C:\dev
git clone --recurse-submodules https://github.com/Natfii/UnrealClaude.git

"C:\Program Files\Epic Games\UE_5.7\Engine\Build\BatchFiles\RunUAT.bat" BuildPlugin ^
  -Plugin="C:\dev\UnrealClaude\UnrealClaude\UnrealClaude.uplugin" ^
  -Package="C:\dev\UnrealClaude\Build" ^
  -TargetPlatforms=Win64
```

### 4-2. 프로젝트에 복사
```bash
xcopy /E /I "C:\dev\UnrealClaude\Build" "MonolithTest\Plugins\UnrealClaude"
```

### 4-3. MCP 브릿지 npm 설치
```bash
cd MonolithTest\Plugins\UnrealClaude\Resources\mcp-bridge
npm install
```

### 4-4. .uproject에 플러그인 추가
```json
{ "Name": "UnrealClaude", "Enabled": true }
```

### 설치 확인
- 에디터에서 Tools > Claude Assistant 메뉴 확인
- `http://localhost:3000/mcp/status` 응답 확인

---

## 5단계: 레포 클론 및 Claude Code 설정

### 5-1. 레포 클론
```bash
cd C:\dev
git clone https://github.com/kanzaka110/Sanjuk-Unreal.git
cd Sanjuk-Unreal
```

### 5-2. .mcp.json 확인
레포에 이미 포함된 `.mcp.json`에 3개 MCP 서버가 등록되어 있음:
- monolith: `http://localhost:9316/mcp`
- unreal-mcp: `npx -y @runreal/unreal-mcp`
- unrealclaude-bridge: node → `http://localhost:3000` (INJECT_CONTEXT=true)

> unrealclaude-bridge의 args에 절대경로가 있으므로 새 PC에서는 경로 수정 필요

### 5-3. Claude Code 전역 규칙 복원 (선택)
```bash
xcopy /E /I "백업경로\.claude-rules" "%USERPROFILE%\.claude\rules"
```

---

## 6단계: 연결 확인

### 6-1. UE 에디터 실행
- MonolithTest 프로젝트를 UE 5.7로 열기
- Monolith + UnrealClaude 플러그인 활성화 확인

### 6-2. Claude Code MCP 연결 테스트
```bash
cd C:\dev\Sanjuk-Unreal
claude
# /mcp 명령으로 3개 MCP 서버 상태 확인
```

---

## 체크리스트 요약

| # | 항목 | 확인 |
|---|------|------|
| 1 | Git 설치 및 사용자 설정 | |
| 2 | Node.js LTS 설치 | |
| 3 | .NET Framework 4.8.1 Developer Pack 설치 | |
| 4 | Claude Code 설치 | |
| 5 | UE 5.7 설치 | |
| 6 | Monolith → 엔진 Plugins/ 또는 환경변수 경로 | |
| 7 | UnrealClaude → 소스 빌드 → 프로젝트 Plugins/ 복사 | |
| 8 | UnrealClaude MCP 브릿지 npm install | |
| 9 | `git clone Sanjuk-Unreal` | |
| 10 | .mcp.json 경로 확인 (unrealclaude-bridge) | |
| 11 | UE 에디터 → Monolith + UnrealClaude 활성화 | |
| 12 | Claude Code `/mcp` → 3개 서버 connected | |
| 13 | Python Remote Execution 활성화 (runreal용) | |

---

## 멀티 PC 확장 (Phase 2 — 필요시)

Tailscale을 사용하여 다른 PC의 UE 에디터를 원격 제어:
1. 모든 PC에 Tailscale 설치 → 같은 계정 로그인
2. `.mcp.json`의 URL을 Tailscale IP로 변경
3. Monolith/UnrealClaude가 `0.0.0.0`에 바인딩하는지 확인 필요
