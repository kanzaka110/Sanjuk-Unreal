---
name: 리모트 세션 듀얼 운영
description: GCP + 로컬 PC 두 세션 동시 운영, 모바일 claude.ai/code 접속 구성
type: project
originSessionId: 6f1162ab-ff22-4389-a3e7-9f4fdf533db6
---
GCP VM과 로컬 PC에서 Claude Code remote-control 두 세션 동시 운영 중.

**세션 구성:**
- Sanjuk-Unreal (Local) — 로컬 PC, Monolith/UE 에디터 제어 가능
- Sanjuk-Unreal (GCP) — GCP VM (sanjuk-project), 문서 작업 전용, PC 꺼져도 접근 가능

**GCP 설정:**
- 레포 경로: /home/ohmil/Sanjuk-Unreal/
- tmux 세션: `unreal`
- 재시작: `scripts/gcp-restart-remote.sh`

**동기화 전략:**
- 대화 컨텍스트 → CLAUDE.md에 기록 (git push/pull로 전 세션 공유)
- Memory → /push 시 로컬→GCP, /pull 시 GCP→로컬 (gcloud compute scp 사용)
- 글로벌 룰 → /push 시 변경분만 GCP로 동기화
- 파일 변경 → git push/pull로 동기화

**경로 매핑:**
- 로컬 메모리: `~/.claude/projects/C--dev-Sanjuk-Unreal/memory/`
- GCP 메모리: `/home/ohmil/.claude/projects/-home-ohmil-Sanjuk-Unreal/memory/`

**Why:** 모바일에서 언제든 작업 가능하도록. PC on/off 상태에 따라 적절한 세션 선택.
**How to apply:** 중요한 컨텍스트는 반드시 CLAUDE.md에도 기록할 것. GCP 세션 시작 시 git pull 먼저.
