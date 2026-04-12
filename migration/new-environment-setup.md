# 새 환경 세팅 완전 가이드

> 새 PC 또는 새 Claude 계정으로 이전할 때의 전체 작업 순서.
> 최종 업데이트: 2026-04-12

---

## 전체 흐름 요약

```
[현재 PC] backup.sh → git push
                ↓
         ┌──── GitHub ────┐
         │                │
    git clone        git clone
         │                │
    [새 PC]          [GCP VM]
         │
    restore.sh → claude 로그인 → /doctor
```

---

## Phase 0: 현재 PC에서 최종 백업 (이전 당일)

> 이미 완료됨 (2026-04-12). 이전 직전 변경사항이 있으면 다시 실행.

### 0-1. 최신 스냅샷 생성

```bash
cd C:/dev/Sanjuk-Unreal
bash migration/backup.sh
```

결과 확인: `migration/snapshot/` 아래 31개+ 파일 생성

### 0-2. GitHub에 푸시

```bash
git add migration/snapshot/
git commit -m "chore: 마이그레이션 최종 스냅샷"
git push origin master
```

### 0-3. GCP에도 동기화

```bash
gcloud compute ssh sanjuk-project --zone=us-central1-b \
  --command='cd /home/ohmil/Sanjuk-Unreal && git pull origin master'
```

### 0-4. 확인 체크리스트

- [ ] GitHub에 최신 커밋 반영됨
- [ ] `migration/snapshot/memory/` — 메모리 23개 포함
- [ ] `migration/snapshot/global-rules/` — 글로벌 룰 7개 포함
- [ ] `migration/snapshot/settings.local.json.tpl` — 플레이스홀더 치환됨
- [ ] `migration/snapshot/mcp.json.tpl` — UE 프로젝트 경로 플레이스홀더

---

## Phase 1: 새 PC 기본 도구 설치

### 1-1. Git

1. https://git-scm.com 에서 다운로드 & 설치
2. Git Bash 또는 터미널에서 설정:
   ```bash
   git config --global user.name "kanzaka110"
   git config --global user.email "<이메일>"
   ```
3. GitHub 인증 설정:
   ```bash
   # HTTPS 방식 (권장)
   git config --global credential.helper manager
   # 또는 SSH 키 생성
   ssh-keygen -t ed25519 -C "<이메일>"
   ```

### 1-2. Node.js

1. https://nodejs.org 에서 **LTS** 버전 설치
2. 설치 확인:
   ```bash
   node --version    # v20+ 이상
   npm --version
   npx --version     # runreal MCP에 필요
   ```

### 1-3. Python

1. https://python.org 에서 3.10+ 설치
2. PATH에 추가 체크 (설치 시 옵션)
3. 확인:
   ```bash
   python --version
   pip --version
   ```

### 1-4. Google Cloud CLI (GCP 사용 시)

1. https://cloud.google.com/sdk/docs/install 에서 설치
2. 인증:
   ```bash
   gcloud auth login
   gcloud config set project sanjuk-project
   ```
3. VM 접속 테스트:
   ```bash
   gcloud compute ssh sanjuk-project --zone=us-central1-b
   ```

### 1-5. Claude Code

**방법 A: npm (CLI)**
```bash
npm install -g @anthropic-ai/claude-code
```

**방법 B: 데스크톱 앱**
- Windows: 공식 사이트에서 다운로드

설치 확인:
```bash
claude --version
```

---

## Phase 2: UE5 에디터 + 플러그인 설치

### 2-1. Unreal Engine 5.7

1. **Epic Games Launcher** 설치 — https://www.unrealengine.com
2. 라이브러리 탭 → UE 5.7 설치
3. 설치 경로 확인 (예: `C:\Program Files\Epic Games\UE_5.7\`)

### 2-2. UE5 프로젝트 생성

1. UE 5.7로 새 프로젝트 생성 (또는 기존 프로젝트 복사)
2. 프로젝트 경로 기록 — 이후 `env.local`에 사용
   ```
   예: C:\Users\<유저>\OneDrive\문서\Unreal Projects\MonolithTest
   ```

### 2-3. Monolith 플러그인 설치

> **핵심: 회사 P4에 올라가지 않도록 엔진 레벨에 설치**

**방법 A: 엔진 Plugins 폴더 (추천)**

1. Fab (https://fab.com) 에서 Monolith 검색 & 다운로드
2. 압축 해제 위치:
   ```
   C:\Program Files\Epic Games\UE_5.7\Engine\Plugins\Marketplace\Monolith\
   ```
3. 에디터 재시작 → Edit > Plugins에서 Monolith 활성화

**방법 B: 독립 경로 + 환경변수**

1. 임의 경로에 설치:
   ```
   C:\MyLocalPlugins\Monolith\
   ```
2. 시스템 환경변수 추가:
   ```
   변수명: UE_ADDITIONAL_PLUGIN_DIRS
   값:     C:\MyLocalPlugins
   ```

**설치 확인:**
- UE 에디터 실행 후 `Edit > Plugins`에서 "Monolith" 검색
- 브라우저에서 `http://localhost:9316/mcp` 접속 → 응답 확인

### 2-4. UnrealClaude 플러그인 설치 (선택)

1. **.NET Framework 4.8.1 Developer Pack** 설치:
   ```bash
   winget install Microsoft.DotNet.Framework.DeveloperPack_4
   ```

2. **소스 클론 & 빌드:**
   ```bash
   cd C:\dev
   git clone --recurse-submodules https://github.com/Natfii/UnrealClaude.git

   "C:\Program Files\Epic Games\UE_5.7\Engine\Build\BatchFiles\RunUAT.bat" BuildPlugin ^
     -Plugin="C:\dev\UnrealClaude\UnrealClaude\UnrealClaude.uplugin" ^
     -Package="C:\dev\UnrealClaude\Build" ^
     -TargetPlatforms=Win64
   ```

3. **프로젝트에 복사:**
   ```bash
   xcopy /E /I "C:\dev\UnrealClaude\Build" "<프로젝트경로>\Plugins\UnrealClaude"
   ```

4. **MCP 브릿지 npm 설치:**
   ```bash
   cd <프로젝트경로>\Plugins\UnrealClaude\Resources\mcp-bridge
   npm install
   ```

5. **.uproject에 플러그인 추가:**
   ```json
   { "Name": "UnrealClaude", "Enabled": true }
   ```

**설치 확인:**
- 에디터에서 `Tools > Claude Assistant` 메뉴 존재
- `http://localhost:3000` 응답 확인

---

## Phase 3: Sanjuk-Unreal 레포 클론 & 복원

### 3-1. 레포 클론

```bash
cd C:\dev
git clone https://github.com/kanzaka110/Sanjuk-Unreal.git
cd Sanjuk-Unreal
```

클론 시 자동으로 가져와지는 파일:
- `.claude/commands/` — 슬래시 명령어 9개
- `.claude/hooks/` — 훅 스크립트 3개
- `.claude/rules/` — UE 전용 룰 6개
- `CLAUDE.md` — 프로젝트 지침서
- `migration/` — 마이그레이션 패키지

### 3-2. env.local 설정

```bash
cp migration/env.example migration/env.local
```

`migration/env.local`을 텍스트 에디터로 열고 4개 변수 수정:

```bash
# 새 PC의 사용자 홈 (Git Bash 형식)
USER_HOME="/c/Users/새유저명"

# 레포 클론 경로
REPO_ROOT_PATH="C:/dev/Sanjuk-Unreal"

# UE5 프로젝트 경로
UE_PROJECT_ROOT="C:/Users/새유저명/OneDrive/문서/Unreal Projects/MonolithTest"

# (일단 비워두기 — 3-4에서 확인 후 채움)
CLAUDE_PROJECT_KEY=""
```

### 3-3. 복원 스크립트 실행

```bash
bash migration/restore.sh
```

복원되는 항목:
| 항목 | 복원 위치 |
|------|----------|
| 글로벌 룰 7개 | `~/.claude/rules/common/` |
| 메모리 23개 | `~/.claude/projects/<KEY>/memory/` |
| settings.local.json | `.claude/settings.local.json` (경로 치환됨) |
| .mcp.json | `.mcp.json` (경로 치환됨) |

### 3-4. CLAUDE_PROJECT_KEY 확인 & 재조정

1. Claude Code를 한 번 실행:
   ```bash
   cd C:\dev\Sanjuk-Unreal
   claude
   ```
2. 로그인 완료 후 종료 (`/exit`)
3. 실제 프로젝트 키 확인:
   ```bash
   ls ~/.claude/projects/
   ```
4. 표시된 폴더명과 restore.sh가 사용한 키가 다르면:
   - `env.local`의 `CLAUDE_PROJECT_KEY`에 실제 폴더명 입력
   - `bash migration/restore.sh` 재실행
5. 확인:
   ```bash
   ls ~/.claude/projects/<실제키>/memory/
   # → 23개 .md 파일이 보여야 함
   ```

---

## Phase 4: Claude Code 로그인 & 환경 검증

### 4-1. Claude Code 시작

```bash
cd C:\dev\Sanjuk-Unreal
claude
```

**새 Claude 계정인 경우:**
- 새 계정으로 로그인 (이메일/OAuth)
- 이전 계정의 대화 이력은 이전되지 않음 (정상)
- 메모리와 룰은 restore.sh로 이미 복원됨

### 4-2. 메모리 인식 확인

Claude Code 안에서:
```
나에 대해 기억하고 있는 것을 알려줘
```

정상이면 "UE5 애니메이션 TA", "MCP", "Monolith" 등 키워드가 나옴.
인식 안 되면 → Phase 3-4로 돌아가 프로젝트 키 재확인.

### 4-3. /doctor 실행

```
/doctor
```

기대 결과:
| 구분 | 항목 | 기대 상태 |
|------|------|----------|
| MCP | Monolith (9316) | ✅ (에디터 실행 중일 때) |
| MCP | UnrealClaude (3000) | ✅ (설치한 경우) |
| MCP | runreal (stdio) | ✅ (Node.js 설치됨) |
| Git | 로컬 상태 | clean |
| 메모리 | 파일 수 | 23개 |

### 4-4. /ue-status 실행

```
/ue-status
```

기대 결과:
```
🟢 Monolith (16모듈) | 🟢 UnrealClaude | 🟢 runreal — 모든 MCP 정상
```

### 4-5. 훅 동작 확인

Monolith 관련 MCP 도구를 호출해서 Pre/PostToolUse 훅이 작동하는지 확인.
- 에디터 꺼진 상태에서 호출 → "Monolith MCP 서버 미응답" 경고가 뜨면 정상

---

## Phase 5: GCP 리모트 세션 복구 (선택)

### 5-1. GCP CLI 인증

```bash
gcloud auth login
gcloud config set project sanjuk-project
```

### 5-2. VM 접속 테스트

```bash
gcloud compute ssh sanjuk-project --zone=us-central1-b
```

### 5-3. GCP 레포 상태 확인

```bash
# VM 안에서
cd /home/ohmil/Sanjuk-Unreal
git status
git log --oneline -3
```

### 5-4. GCP 메모리 동기화

```bash
# 로컬에서 실행
gcloud compute scp --zone=us-central1-b --recurse \
  ~/.claude/projects/<프로젝트키>/memory/ \
  sanjuk-project:/home/ohmil/.claude/projects/-home-ohmil-Sanjuk-Unreal/memory/
```

### 5-5. GCP Claude Code 리모트 세션 재시작

```bash
# VM에 SSH 접속 후
tmux new-session -s unreal
cd /home/ohmil/Sanjuk-Unreal
claude
# 로그인 (새 계정이면 새로 인증)
```

모바일 claude.ai/code에서 GCP 세션 접속 확인.

---

## Phase 6: CLAUDE.md 경로 업데이트

새 PC의 경로가 바뀌었으면 CLAUDE.md의 경로 정보를 수정:

### 6-1. UE5 프로젝트 경로

```markdown
## UE5 프로젝트 환경
- UE 프로젝트 경로: `C:\Users\<새유저>\OneDrive\문서\Unreal Projects\`
```

### 6-2. MonolithTest 경로

문서 전체에서 `C:\Users\ohmil\`을 새 경로로 치환.

### 6-3. 커밋 & 동기화

```bash
git add CLAUDE.md
git commit -m "chore: 새 환경 경로 반영"
git push origin master
# GCP도 동기화
/push
```

---

## 트러블슈팅

### 문제 1: 메모리가 인식되지 않음

**원인:** CLAUDE_PROJECT_KEY 불일치
```bash
# 실제 키 확인
ls ~/.claude/projects/

# 메모리 수동 복사
cp migration/snapshot/memory/*.md ~/.claude/projects/<실제키>/memory/
```

### 문제 2: Monolith MCP 연결 실패

**확인 순서:**
1. UE 에디터가 실행 중인가?
2. Monolith 플러그인이 활성화되어 있는가? (`Edit > Plugins`)
3. 포트 확인: `curl http://localhost:9316/mcp`
4. 방화벽이 9316 포트를 차단하고 있지 않은가?

**복구:**
```
/recover
```

### 문제 3: UnrealClaude 브릿지 연결 실패

**확인 순서:**
1. Node 프로세스 확인: `tasklist | grep node`
2. .mcp.json의 경로가 정확한가?
   ```bash
   cat .mcp.json
   # unrealclaude-bridge의 args 경로 확인
   ```
3. MCP 브릿지 npm install이 완료되었는가?

### 문제 4: GCP VM 접속 불가

**확인 순서:**
1. `gcloud auth list` — 인증 상태 확인
2. VM이 실행 중인가?
   ```bash
   gcloud compute instances list
   ```
3. VM이 중지 상태면:
   ```bash
   gcloud compute instances start sanjuk-project --zone=us-central1-b
   ```

### 문제 5: Git push 권한 없음 (계정 변경)

**새 GitHub 계정 사용 시:**
1. 기존 레포를 Fork하거나 Collaborator 추가
2. 또는 remote URL 변경:
   ```bash
   git remote set-url origin https://github.com/<새계정>/Sanjuk-Unreal.git
   ```

### 문제 6: settings.local.json 경로가 맞지 않음

```bash
# restore.sh 재실행
bash migration/restore.sh

# 또는 수동으로 경로 치환
# .claude/settings.local.json 열어서 경로 수정
```

---

## 최종 체크리스트

| # | 항목 | 확인 |
|---|------|------|
| 1 | Git 설치 & 사용자 설정 | ☐ |
| 2 | Node.js LTS 설치 | ☐ |
| 3 | Python 3.10+ 설치 | ☐ |
| 4 | Claude Code 설치 | ☐ |
| 5 | Google Cloud CLI 설치 & 인증 | ☐ |
| 6 | UE 5.7 설치 | ☐ |
| 7 | UE5 프로젝트 생성/복사 | ☐ |
| 8 | Monolith 플러그인 설치 (엔진 레벨) | ☐ |
| 9 | UnrealClaude 빌드 & 설치 (선택) | ☐ |
| 10 | `git clone Sanjuk-Unreal` | ☐ |
| 11 | `env.local` 편집 | ☐ |
| 12 | `bash migration/restore.sh` 실행 | ☐ |
| 13 | Claude Code 로그인 | ☐ |
| 14 | CLAUDE_PROJECT_KEY 확인 & 재조정 | ☐ |
| 15 | 메모리 인식 확인 | ☐ |
| 16 | `/doctor` 통과 | ☐ |
| 17 | `/ue-status` 통과 | ☐ |
| 18 | CLAUDE.md 경로 업데이트 | ☐ |
| 19 | GCP 세션 복구 (선택) | ☐ |
| 20 | `/push`로 전체 동기화 | ☐ |

---

## 소요 시간 추정

| Phase | 내용 | 비고 |
|-------|------|------|
| Phase 0 | 현재 PC 백업 | 이미 완료 |
| Phase 1 | 기본 도구 설치 | UE5 다운로드가 가장 오래 걸림 |
| Phase 2 | UE5 + 플러그인 | Monolith Fab 다운로드 + UnrealClaude 빌드 |
| Phase 3 | 레포 클론 & 복원 | restore.sh 1분 이내 |
| Phase 4 | 검증 | /doctor + /ue-status |
| Phase 5 | GCP 복구 | gcloud 인증만 하면 즉시 |
| Phase 6 | 경로 업데이트 | CLAUDE.md 수정 + 커밋 |
