# 02. 설치 가이드

## 사전 요구사항

| 항목 | 최소 버전 | 확인 방법 |
|------|----------|----------|
| Node.js | 18 이상 | `node -v` |
| npm | 8 이상 | `npm -v` |
| Unreal Engine | 5.4 이상 | 에디터 하단 상태바 |

## Step 1: Node.js 설치 확인

터미널(PowerShell 또는 CMD)을 열고:

```bash
node -v
# 출력 예: v24.14.0

npm -v
# 출력 예: 11.9.0
```

Node.js가 없다면 https://nodejs.org 에서 LTS 버전을 다운로드하세요.

## Step 2: runreal 글로벌 설치

```bash
npm install -g @runreal/unreal-mcp
```

설치 확인:
```bash
npm list -g @runreal/unreal-mcp
# 출력 예: └── @runreal/unreal-mcp@0.1.4
```

### 글로벌 설치 vs npx

| 방법 | 명령어 | 장점 | 단점 |
|------|--------|------|------|
| **글로벌 설치** | `npm install -g @runreal/unreal-mcp` | 빠른 실행, 오프라인 가능 | 수동 업데이트 필요 |
| **npx (매번 다운로드)** | `npx -y @runreal/unreal-mcp` | 항상 최신, 설치 불필요 | 첫 실행 느림 |

이미 글로벌 설치했다면 MCP 설정에서 `npx` 대신 직접 경로를 사용할 수도 있습니다.

## Step 3: 설치 경로 확인

```bash
# Windows
npm root -g
# 출력 예: C:\Users\{사용자}\AppData\Roaming\npm\node_modules

# 실행 파일 위치
where unreal-mcp 2>nul || echo "글로벌 bin에 등록되지 않음 (npx로 실행)"
```

## Step 4: 동작 테스트 (UE 없이)

```bash
npx @runreal/unreal-mcp
```

UE 에디터가 안 켜져 있으면 아래처럼 나옵니다 - **이것이 정상**입니다:

```
Connection attempt 1 failed: Error: Timed out
Retrying in 2000ms...
Connection attempt 2 failed: Error: Timed out
Retrying in 3000ms...
Connection attempt 3 failed: Error: Timed out
Unable to connect to your Unreal Engine Editor after multiple attempts
```

3회 재시도 후 종료됩니다. UE 에디터를 켜고 Python Remote Execution을 활성화하면 연결됩니다.

## Step 5: 업데이트 방법

```bash
# 글로벌 설치 업데이트
npm update -g @runreal/unreal-mcp

# 현재 버전 확인
npm list -g @runreal/unreal-mcp

# npx 캐시 정리 (npx 사용 시)
npx clear-npx-cache
```

## Step 6: 제거 방법

```bash
npm uninstall -g @runreal/unreal-mcp
```

프로젝트 파일이나 UE 에디터에 아무것도 설치하지 않았으므로, npm 제거만 하면 완전히 깨끗합니다.

## 다음 단계

설치가 끝났으면 [03. UE5 에디터 설정](03-UE5-Editor-Setup.md)으로 이동하세요.
