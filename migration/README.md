# Claude Code + UE5 환경 마이그레이션 가이드

새 PC 또는 새 Claude 계정으로 이전할 때 사용.

## 이전되는 항목

| 항목 | 저장 방식 | 이전 방법 |
|------|----------|----------|
| 슬래시 명령어 (9개) | git 추적 | `git clone` 시 자동 |
| 훅 스크립트 (3개) | git 추적 | `git clone` 시 자동 |
| 프로젝트 룰 (6개) | git 추적 | `git clone` 시 자동 |
| CLAUDE.md | git 추적 | `git clone` 시 자동 |
| 글로벌 룰 (7개) | 스냅샷 | `restore.sh`로 복원 |
| 메모리 (22개) | 스냅샷 | `restore.sh`로 복원 |
| settings.local.json | 템플릿 | `restore.sh`로 경로 치환 |
| .mcp.json | 템플릿 | `restore.sh`로 경로 치환 |

## 현재 PC에서 백업 (이전 전)

```bash
cd C:/dev/Sanjuk-Unreal

# 1. 백업 실행
bash migration/backup.sh

# 2. 스냅샷 커밋 & 푸시
git add migration/snapshot/
git commit -m "chore: 마이그레이션 스냅샷 백업"
git push origin master
```

## 새 PC에서 복원

### 사전 설치 (수동)

1. **Git** — https://git-scm.com
2. **Node.js LTS** — https://nodejs.org
3. **Claude Code** — `npm install -g @anthropic-ai/claude-code` 또는 데스크톱 앱
4. **UE 5.7** — Epic Games Launcher
5. **Monolith 플러그인** — Fab에서 다운로드 → 엔진 Plugins/ 설치
6. **UnrealClaude** — GitHub 클론 → 빌드 → 프로젝트 Plugins/ 복사

### 자동 복원

```bash
# 1. 레포 클론
cd C:/dev
git clone https://github.com/kanzaka110/Sanjuk-Unreal.git
cd Sanjuk-Unreal

# 2. 환경 변수 설정
cp migration/env.example migration/env.local
# env.local 편집: USER_HOME, REPO_ROOT_PATH, UE_PROJECT_ROOT 수정

# 3. 복원 실행
bash migration/restore.sh

# 4. Claude Code 시작 & 로그인
claude
# 로그인 완료 후:
# /doctor 실행하여 환경 점검
```

### 복원 후 수동 확인

- [ ] `claude` 실행 시 글로벌 룰 7개 로드되는지 확인
- [ ] 메모리 인식 여부 확인 ("기억해?" 등으로 테스트)
- [ ] `/doctor` 실행하여 MCP 3개 연결 상태 확인
- [ ] `/ue-status` 실행하여 에디터 연결 확인

## CLAUDE_PROJECT_KEY 확인 방법

Claude Code는 레포 경로를 기반으로 프로젝트 키를 생성합니다:

```
경로: C:\dev\Sanjuk-Unreal
 키: C--dev-Sanjuk-Unreal

경로: /home/user/Sanjuk-Unreal
 키: -home-user-Sanjuk-Unreal
```

정확한 키는 Claude Code를 한 번 실행한 후 `~/.claude/projects/` 아래 생성된 폴더명을 확인하세요.

만약 메모리가 인식되지 않으면:
1. `~/.claude/projects/` 아래 실제 폴더명 확인
2. `env.local`의 `CLAUDE_PROJECT_KEY` 수정
3. `bash migration/restore.sh` 재실행

## Claude 계정 변경 시 추가 조치

- 계정이 바뀌어도 git에 저장된 파일은 그대로 유지됨
- `~/.claude/` 아래 파일만 재복원 필요 → `restore.sh` 실행
- GCP 세션은 별도 재설정 필요 (동일 GCP 계정이면 `gcloud auth login`만)

## GCP 세션 복구

```bash
# GCP CLI 인증
gcloud auth login

# VM 접속 테스트
gcloud compute ssh sanjuk-project --zone=us-central1-b

# tmux 세션 확인
tmux attach -t unreal
```
