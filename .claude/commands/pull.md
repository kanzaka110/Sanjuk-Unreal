# 풀 — 전체 동기화 (외부 → 로컬)

GitHub/GCP에 올라간 최신 변경사항을 로컬로 가져와 동기화하는 명령어.

## 실행 순서

### 1단계: 로컬 상태 확인
- `git status`로 로컬에 커밋되지 않은 변경사항이 있는지 확인
- 변경사항이 있으면 사용자에게 알림 (stash 또는 커밋 여부 확인)

### 2단계: GitHub에서 풀
- `git fetch origin`으로 원격 변경사항 확인
- `git log HEAD..origin/master --oneline`으로 새 커밋 목록 표시
- 새 커밋이 있으면 `git pull origin master`로 가져오기
- 충돌이 있으면 사용자에게 보고하고 해결 방안 제시

### 3단계: 변경사항 분석
- 풀한 커밋들의 내용을 요약
- 어떤 파일이 추가/수정/삭제되었는지 보고
- CLAUDE.md가 변경되었으면 내용 확인 후 반영

### 4단계: 메모리 동기화
- **GCP → 로컬 메모리 가져오기:** GCP에서 새로 추가/수정된 메모리 확인
  ```
  gcloud compute scp --zone=us-central1-b \
    sanjuk-project:/home/ohmil/.claude/projects/-home-ohmil-Sanjuk-Unreal/memory/* \
    ~/.claude/projects/C--dev-Sanjuk-Unreal/memory/
  ```
- 가져온 메모리 중 로컬과 충돌하는 것이 있으면 내용 비교 후 병합
- 풀한 git 내용 중 메모리에 반영할 새 정보가 있는지 확인
- 프로젝트 구조, MCP 설정, 작업 환경 변경 등이 있으면 메모리 업데이트

### 5단계: 결과 요약

| 항목 | 상태 |
|------|------|
| 로컬 변경사항 | 없음/stash됨/커밋됨 |
| GitHub 풀 | N개 커밋 가져옴/최신 상태 |
| 변경 파일 | 목록 또는 "없음" |
| 메모리 | 업데이트됨/변경없음 |
