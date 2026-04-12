---
name: GCP 자동 동기화 필수
description: 로컬에서 작업 후 항상 GCP로 메모리/룰/git 동기화 — 다른 환경에서 동일 경험 보장
type: feedback
originSessionId: 6f1162ab-ff22-4389-a3e7-9f4fdf533db6
---
로컬에서 작업이 이뤄지면 항상 GCP로 동기화해야 한다.

**Why:** 사용자가 GCP, 모바일, 다른 PC 등 어디서든 pull 받아서 동일한 환경/정보로 Claude Code를 사용하고 싶어함. 메모리, 룰, git 변경이 한쪽에만 남아있으면 다른 세션에서 맥락이 끊김.

**How to apply:**
- 세션 중 메모리를 수정/추가하면 → 즉시 또는 세션 끝에 GCP로 scp
- 세션 중 git 변경이 있으면 → push 후 GCP에서도 git pull
- 글로벌 룰(~/.claude/rules/common/) 변경 시 → GCP로 scp
- `/push` 실행 시 자동으로 위 모든 것이 포함됨
- 동기화 대상 경로:
  - 메모리: `~/.claude/projects/C--dev-Sanjuk-Unreal/memory/` → GCP `/home/ohmil/.claude/projects/-home-ohmil-Sanjuk-Unreal/memory/`
  - 룰: `~/.claude/rules/common/` → GCP `/home/ohmil/.claude/rules/common/`
  - Git: `git push` → GCP `git pull`
