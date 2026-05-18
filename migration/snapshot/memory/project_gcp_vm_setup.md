---
name: GCP VM (sanjuk-project) 리모트 환경 주의사항
description: e2-small 2GB RAM 제약, .claude 소유권 버그, 여러 remote-control 세션 공존 환경
type: project
originSessionId: abee917a-80bb-4cf4-a80c-e01a5e7ce6da
---
## 스펙
- `sanjuk-project` @ `us-central1-b` — **e2-small (2 vCPU, 2GB RAM)**
- 한국 RTT ~150ms. 서울 리전 아님.
- 메모리 상시 90%+, swap 사용 중 — 체감 속도 저하의 주원인은 swap IO.

## 동시 가동 tmux 세션 (ohmil)
- `unreal` — Sanjuk-Unreal (GCP)
- `claude` — Sanjuk-Stock-Simulator (GCP)
- `max3d` — 3dsmax-mcp-GCP
- `ecc` — Sanjuk-Telegram-Bot (kanzaka110 유저)

각 claude remote-control 프로세스 ~100–210MB. 4개 동시 = 2GB RAM 부족.

## `.claude` / `Sanjuk-Unreal/.git` 소유권 — gcloud SSH user는 SHIFTUP

**핵심 사실 (2026-04-29 확정):**
- `gcloud compute ssh sanjuk-project` 의 SSH session user = **`SHIFTUP` (uid=1002, gid=1005)**
- `/home/ohmil/` 디렉토리는 ohmil 소유였으나, 실제 작업은 SHIFTUP user로 이뤄짐 → 권한 충돌
- 즉 GCP의 ohmil 디렉토리들은 **SHIFTUP 소유로 두는 게 맞음** (메모리에 기록된 "ohmil:ohmil로 chown" 방향은 잘못)

**증상:**
- `git pull` → `error: cannot open '.git/FETCH_HEAD': Permission denied`
- `gcloud compute scp` → `pscp: unable to open ...: permission denied`
- `claude remote-control` 기동 시 "You must be logged in"

**복구 명령 (검증됨):**
```bash
gcloud compute ssh sanjuk-project --zone=us-central1-b \
  --command='sudo -n chown -R SHIFTUP:SHIFTUP /home/ohmil/.claude /home/ohmil/Sanjuk-Unreal'
```
- SHIFTUP은 google-sudoers 그룹 멤버라 `sudo -n` 패스워드 없이 가능
- chown 후 즉시 git pull / scp 모두 정상 동작

**Why:** gcloud SSH key가 SHIFTUP user에 매핑됨 (Windows 로그온 user). ohmil 소유로는 SSH user가 못 읽음.
**How to apply:** GCP에서 git pull/scp 권한 거부 시 위 명령 1회 실행. 이전에 메모리에 기록된 "ohmil:ohmil로 chown"은 반대 방향이라 효과 없음 (SHIFTUP이 다시 못 읽음).

## 재시작 명령
```bash
gcloud compute ssh ohmil@sanjuk-project --zone=us-central1-b \
  --command="bash ~/Sanjuk-Unreal/scripts/gcp-restart-remote.sh"
```
- 주의: `--command` 없이 stdin 리다이렉트로 스크립트 전달은 plink(Windows)에서 실패. `--command="bash ~/..."` 패턴 써야 함.

## 체감 속도 개선 옵션
1. 안 쓰는 tmux 세션 종료 (효과 제한적, claude 프로세스당 100MB 수준)
2. VM 업그레이드 → `e2-medium (4GB)` 이상 권장
3. 서울 리전(`asia-northeast3`) 이전 — 네트워크 RTT 개선
