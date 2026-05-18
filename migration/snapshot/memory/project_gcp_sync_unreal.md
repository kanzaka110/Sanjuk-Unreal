---
name: GCP 동기화 - Sanjuk-Unreal 확장
description: Sanjuk-Unreal 메모리가 GCP에 memory-unreal/ 폴더로 동기화되도록 claude-sync.sh 확장 완료
type: project
originSessionId: 39f100c7-5cb2-4d29-8ac3-476cb7351b2e
---
2026-04-19 기존 `C:/dev/Sanjuk-Claude-Code/scripts/claude-sync.sh`에 Sanjuk-Unreal 메모리 동기화 경로를 추가.

**Why:** 기존 sync 스크립트는 `C--dev-Sanjuk-Claude-Code/memory/`만 동기화해서 Sanjuk-Unreal 메모리는 GCP에 올라가지 않았음. 사용자가 "기존 sync 확장" 방식 선택.

**How to apply:**
- 로컬 경로: `~/.claude/projects/C--dev-Sanjuk-Unreal/memory/`
- GCP 경로: `/home/ohmil/claude-sync/memory-unreal/`
- Claude-Code 메모리 경로(`memory/`)는 그대로 유지 — 두 프로젝트 분리 관리
- 훅(`~/.claude/settings.json`의 UserPromptSubmit/PostToolUse)은 그대로 사용 — 메모리 편집 시 양쪽 모두 업로드됨
- `bash scripts/claude-sync.sh {upload|download|status}` 세 명령 모두 두 프로젝트 동시 처리
- 동기화 스크립트 자체는 Sanjuk-Claude-Code 리포에 있음 (공용 인프라로 취급)
