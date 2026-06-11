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

### 4단계: GCP + Hermes 동기화

> ⚠ SSH는 반드시 `kanzaka110@` 유저. bare `sanjuk-project` 는 권한 거부됨 (CLAUDE.md 리모트 세션 규칙).

#### 4a. GCP Git 동기화
```
gcloud compute ssh kanzaka110@sanjuk-project --zone=us-central1-b \
  --command='cd /home/kanzaka110/Sanjuk-Unreal && git pull origin master'
```
- pull 이 로컬 변경 충돌로 abort 되면 → **강제 진행 금지.** GCP 작업트리 변경 내용을 먼저 보고하고 사용자 판단 대기 (stash / commit / discard 중 선택).

#### 4b. Hermes 메모리 동기화 (핵심)
Hermes 가 읽는 원본은 `/home/kanzaka110/claude-sync/memory-unreal/` (소유자 SHIFTUP, 매시간 cron rsync 로 Hermes 로 운반). 디렉토리가 kanzaka110 쓰기 불가라 **tmp 경유 + sudo cp** 패턴 사용. `--delete` 금지 (GCP-only 메모리 보존).
```
# 1) 로컬 메모리를 GCP tmp 로 업로드
gcloud compute ssh kanzaka110@sanjuk-project --zone=us-central1-b \
  --command='rm -rf ~/mem_sync_tmp && mkdir -p ~/mem_sync_tmp'
gcloud compute scp --recurse --zone=us-central1-b \
  "C:/Users/SHIFTUP/.claude/projects/C--Dev-Sanjuk-Unreal/memory" \
  kanzaka110@sanjuk-project:/home/kanzaka110/mem_sync_tmp/

# 2) sudo cp 로 Hermes 원본에 반영 + 소유권/권한 정렬 + tmp 정리
gcloud compute ssh kanzaka110@sanjuk-project --zone=us-central1-b --command='
  S=~/mem_sync_tmp/memory; D=/home/kanzaka110/claude-sync/memory-unreal;
  sudo cp -f $S/*.md $D/ && sudo chown SHIFTUP:SHIFTUP $D/*.md && sudo chmod 644 $D/*.md;
  rm -rf ~/mem_sync_tmp; echo "반영 후 파일수:"; ls -1 $D/*.md | wc -l'
```
- 반영 후 **즉시 트리거** (2026-06-11부터 SSH 키 등록으로 가능 — cron 대기 불필요):
```
ssh -i ~/.ssh/hermes_ed25519 root@187.77.157.93 "/root/.hermes/sync-gcp.sh 2>&1 | tail -3"
```
- SSH 실패 시 폴백: 다음 정각 cron (`/root/.hermes/sync-gcp.sh`) 자동 수신.
- 참조: [[reference-hermes-gcp-sync]] [[reference-hermes-realtime-send]]

#### 4c. 글로벌 룰 동기화 (변경 시에만, 실패 무시 가능)
```
gcloud compute scp --zone=us-central1-b \
  ~/.claude/rules/common/* \
  kanzaka110@sanjuk-project:/home/kanzaka110/.claude/rules/common/
```
- 동기화 실패 시 오류 보고 (네트워크 / VM 꺼짐 / 권한)

### 5단계: 결과 요약
변경사항과 동기화 상태를 테이블로 요약:

| 항목 | 상태 |
|------|------|
| 메모리 | 업데이트됨/변경없음 |
| CLAUDE.md | 업데이트됨/변경없음 |
| GitHub | 푸시됨/변경없음 |
| GCP Git | 동기화됨/실패(충돌 시 보고)/변경없음 |
| Hermes 메모리 (claude-sync/memory-unreal) | 동기화됨(N개)/실패 — 다음 정각 cron 으로 Hermes 반영 |
| 글로벌 룰 | 동기화됨/실패/변경없음 |
