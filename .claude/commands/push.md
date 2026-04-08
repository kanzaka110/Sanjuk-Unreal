# 푸시 — 전체 동기화 (로컬 → 외부)

메모리, GitHub, GCP 모두 최신 상태로 업데이트하는 원스톱 명령어.

## 실행 순서

### 0단계: Stale Branch 감지 (사전 점검)

푸시 전에 원격과의 동기화 상태를 확인하여 충돌을 예방:

1. `git fetch origin` 실행
2. `git log HEAD..origin/master --oneline` 으로 원격에만 있는 커밋 확인
3. 원격이 앞서 있으면 (커밋이 존재하면):
   - **경고 표시:** "⚠️ origin/master가 N개 커밋 앞서 있습니다"
   - 변경 내용 요약 표시
   - 사용자에게 선택지 제시:
     - `git pull --rebase origin master` 후 계속 진행
     - `/pull` 먼저 실행 후 다시 `/push`
     - 무시하고 강제 진행 (비추천)
   - **사용자 확인 없이 자동으로 진행하지 않음**
4. 동기화 상태이면 → 다음 단계로 진행

### 1단계: 메모리 업데이트
- `~/.claude/projects/C--dev-Sanjuk-Unreal/memory/MEMORY.md` 및 개별 메모리 파일 확인
- 이번 세션에서 새로 알게 된 정보가 있으면 메모리에 반영
- 오래되었거나 부정확한 메모리가 있으면 수정 또는 삭제

### 2단계: CLAUDE.md 점검
- `CLAUDE.md`에 업데이트할 내용이 있는지 확인 (구조 변경, 새 도구 추가 등)
- 필요하면 갱신

### 3단계: Git 커밋 & 푸시
- `git status`로 변경사항 확인
- 변경사항이 있으면:
  - 적절한 커밋 메시지로 커밋 (conventional commits 형식)
  - `git push origin master`로 GitHub에 푸시
- 변경사항이 없으면 "변경사항 없음" 보고

### 4단계: GCP 동기화 안내
- GCP VM에서 `git pull`이 필요함을 안내
- 명령어 제시: `ssh sanjuk-vm 'cd /home/ohmil/Sanjuk-Unreal && git pull'`
- 또는 모바일에서 GCP 세션 접속 후 `git pull` 실행 안내

### 5단계: 결과 요약
변경사항과 동기화 상태를 테이블로 요약:

| 항목 | 상태 |
|------|------|
| 메모리 | 업데이트됨/변경없음 |
| CLAUDE.md | 업데이트됨/변경없음 |
| GitHub | 푸시됨/변경없음 |
| GCP | 수동 pull 필요/변경없음 |
