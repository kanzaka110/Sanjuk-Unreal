---
name: GCP VM 환경 정보
description: Sanjuk-Unreal이 실행되는 GCP VM 환경 및 접속 정보
type: reference
---

GCP 프로젝트: `sanjuk-talk-bot`
VM 이름: `sanjuk-project`
존: `us-central1-b`
서비스 계정: `1053900927638-compute@developer.gserviceaccount.com`

레포 경로: `/home/ohmil/Sanjuk-Unreal/`
Claude 프로젝트 데이터: `/home/ohmil/.claude/projects/-home-ohmil-Sanjuk-Unreal/`
tmux 세션: `unreal` (Claude Code 실행용), `claude` (별도)

스크립트:
- `scripts/gcp-restart-remote.sh` — GCP 리모트 재시작
- `scripts/gcp-setup-remote.sh` — GCP 리모트 셋업
- `scripts/gcp-status.cmd` — GCP 상태 확인 (Windows)
- `scripts/local-remote-control.cmd` — 로컬 리모트 제어 (Windows)

**How to apply:** Claude Code는 이 GCP VM에서 리모트로 실행됨. 로컬(Windows)과 GCP 양쪽에서 작업 가능한 듀얼 환경.
