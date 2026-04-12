---
name: 환경 이전 예정
description: 2026-04-13부터 새 PC/계정으로 이전 예정, migration/ 패키지로 복원
type: project
originSessionId: 119b56cd-4bf6-4f42-a8cb-75582b9396a5
---
2026-04-13부터 새 환경(PC/계정)으로 이전 예정.

**마이그레이션 패키지:** `migration/` 폴더에 backup.sh + restore.sh + snapshot/ 준비 완료.
- 글로벌 룰 7개, 메모리 22개, settings/mcp 템플릿 포함
- 절대 경로는 플레이스홀더로 치환 (USER_HOME, REPO_ROOT, UE_PROJECT_ROOT)

**복원 절차:** git clone → env.local 편집 → bash restore.sh → claude 로그인 → /doctor

**3중 백업:** GitHub + GCP VM + migration/snapshot

**Why:** Claude 계정 변경 시 ~/.claude/ 전체 리셋됨. git 미추적 파일(메모리, 글로벌 룰) 유실 방지.
**How to apply:** 새 환경 첫 세션에서 migration/README.md 참조하여 복원.
