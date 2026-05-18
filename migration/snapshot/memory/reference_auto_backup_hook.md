---
name: auto-backup-hook
description: PostToolUse hook 이 Monolith mutate 액션 감지 시 백그라운드 자동 백업 + monolith_discover 호출 시 카탈로그 자동 갱신. AI 가 백업 잊어도 hook 이 강제.
metadata: 
  node_type: memory
  type: reference
  originSessionId: ea3be7a5-d8f0-4249-af75-76ddb6a92c3d
---

`.claude/hooks/post-monolith-verify.sh` 가 Monolith MCP 응답을 stdin 으로 받아 자동 처리. AI 가 backup 명령 잊어도 hook 이 강제.

**Why:** 2026-05-18 추가. 이전 `/tune-abp` 슬래시 사전 조건은 "AI 가 의식적으로 백업 실행" — 잊으면 ROLLED BACK 5건 같은 비용 재발. hook 자동 트리거로 차단.

## 자동 트리거 패턴

### 1) Mutate 액션 감지 → 백그라운드 자동 백업
응답 본문의 `"action": "<pattern>"` 매칭:
- `set_*` (set_pin_default, set_variable_defaults, set_cdo_property, set_node_position, set_function_params, ...)
- `add_*` (add_node, add_variable, add_function, add_state_to_machine, add_anim_graph_node, ...)
- `remove_*` (remove_node, remove_variable, ...)
- `connect_*` / `disconnect_*` (connect_pins, connect_anim_graph_pins)
- `batch_execute`

**제외**: `save_asset`, `compile_blueprint` (변경 후 시점이라 백업 의미 X)

추출 정보:
- `asset_path` (응답 본문의 `"asset_path": "/Game/..."` 매칭)
- mutate action 이름 → label = `auto_<action>`

실행:
```
(cd <repo> && py scripts/abp_backup.py backup "<asset>" "auto_<action>") &
```
백그라운드 fire-and-forget. 로그: `.claude/state/hook.log`

### 2) Monolith discover/status 응답 → 카탈로그 자동 갱신
응답 본문에 `"total_actions"` 또는 `"namespaces"` 키 감지 시:
```
(cd <repo> && py scripts/save_discover_snapshot.py) &
```
다음 `/doctor` 또는 `/start` 호출 시 fresh 카탈로그 + 히스토리 diff.

## 검증된 동작 (2026-05-18 smoke 6 케이스)

| # | 입력 | 결과 |
|---|---|---|
| 1 | 정상 disconnect 응답 | 통과 (트리거 X) |
| 2 | mutate set_pin_default | ✅ 백업 자동 (hook.log 기록 + .claude/state/backups/PC_01_ABP/<ts>_auto_set_pin_default/ 생성) |
| 3 | save_asset | 통과 (트리거 X, 의도) |
| 4 | monolith_discover 응답 | ✅ 카탈로그 자동 갱신 트리거 |
| 5 | MCP -32601 에러 | ✅ 에러 알림 |
| 6 | isError true | ✅ 에러 알림 |

## 권한
이미 `.claude/settings.local.json` 의 `Bash(py *)` / `Bash(python *)` 가 등록돼 권한 prompt 없이 백그라운드 실행 가능.

## 한계
- **stdin JSON 의 escape 문제**: Claude Code hook 입력은 raw JSON (escape 없음) 가정. mock 테스트 시 `\"` escape 가 들어가면 grep 매칭 실패 — 실 환경에서는 정상
- **백업 폴더 누적**: mutate 마다 백업 → 7일 이상 `py scripts/abp_backup.py prune --days 7` 권장
- **자동 백업은 변수 default 만 안전 복원** ([[reference-abp-backup-system]] 의 unsupported 영역 그대로)
- **hook 자체 실패 시 silent**: stderr 는 hook.log 로 갈음. py 실행 실패 시 백업 안 됨 (Monolith 응답은 정상 통과)

## How to apply
- 사용자가 도구 이름 모르고도 자연어로 작업 요청 → AI 가 Monolith 호출 → mutate 감지 → 자동 백업 → 사용자 무감지
- 다음 작업이 다른 mutate 면 같은 패턴 반복 → 변경 단위마다 백업 보존
- 문제 발생 시 `py scripts/abp_backup.py list <asset>` 로 최근 백업 확인 → `restore --apply` 1줄
- 디스크 정리: 매주 `py scripts/abp_backup.py prune --days 7` (cron / 사용자 수동)

관련 메모리: [[reference-abp-backup-system]], [[reference-visual-verification]], [[absorption-candidates-2026-05-18]].
