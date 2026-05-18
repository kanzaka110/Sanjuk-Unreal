---
name: abp-backup-system
description: "scripts/abp_backup.py + MonolithClient.backup/rollback. Tuner 변경 직전 자동 백업 + 1줄 dry-run/실제 복원. 변수 default 한해 안전 복원, 그래프 토폴로지는 자동 복원 불가."
metadata: 
  node_type: memory
  type: reference
  originSessionId: ea3be7a5-d8f0-4249-af75-76ddb6a92c3d
---

ABP 변경 작업 (`/tune-abp`, set_cdo_property, batch_execute 등) 직전 자동 백업 + 변경 후 1줄 롤백.

**Why:** 2026-05-18 추가. 이전 [[pc01-smoothing-to-zero-revert]], [[pc01-transition-gate-phase1]] 등 ROLLED BACK 메모리 5건이 매번 매뉴얼 학습 — 자동화로 비용 ↓.

## 백업 위치
```
.claude/state/backups/<ASSET_NAME>/<TIMESTAMP>[_<label>]/
  ├── _meta.json          (asset / timestamp / label / created_at)
  ├── abp_info.json       (skeleton/graph_count/var_count/interfaces)
  ├── state_machines.json (SM 전체 + transitions 요약)
  ├── transitions.json    (전체 transition + rule_nodes chain)
  └── variables.json      (변수 목록 + defaults)
```
gitignore 처리 (`.claude/*`).

## CLI 4 subcommand

```bash
py scripts/abp_backup.py backup  <asset> [label]      # 새 백업
py scripts/abp_backup.py list    <asset>              # 백업 목록 (timestamp 역순)
py scripts/abp_backup.py diff    <asset> <ts|label>   # 현재 vs 백업 비교
py scripts/abp_backup.py restore <asset> <ts|label> [--apply]   # dry-run 기본, --apply 로 실제
py scripts/abp_backup.py prune   <asset> [--days 7]   # 오래된 백업 삭제
```

Git Bash MSYS path 변환 (`/Game/...` → `C:/Program Files/Git/Game/...`) 자동 복구 내장.

## MonolithClient API (헬퍼 모듈)

```python
from monolith_helpers import MonolithClient

cli = MonolithClient(asset)
backup = cli.backup(label="istransition-test")
# ... 변경 작업 ...
diff = cli.diff_against_backup("istransition-test")
plan = cli.rollback("istransition-test", dry_run=True)  # 또는 False
```

## 자동 복원 가능 영역 (안전)
- ✅ 변수 default 복원 — `set_variable_defaults` 로 1:1 복원
- ✅ compile + save 자동 수반

## 자동 복원 불가 영역 (사용자 수동)
- ❌ 신규 추가된 변수 자동 제거 — type 정보 손실 위험
- ❌ 신규 추가/제거된 노드 — Monolith add_node/remove_node 로 부분 가능하나 핀 연결 복원 불완전
- ❌ Transition rule chain 토폴로지 — Monolith 한계 ([[reference-monolith-animgraph-editing-limits]])
- ❌ Chooser ResultsStructs 변경 — protected ([[feedback-sb2-python-plugin-disabled]] 해제 시 우회 가능성)
- → 위 영역은 plan["unsupported"] 에 명시되어 사용자에게 노출

## 자동 호출 시점 (워크플로우 내장)

`/tune-abp` 슬래시는 사전 조건으로 백업 1회 강제 실행 명시 ([[reference-animgraph-node-editing]] 의 IsTransition gate 같은 큰 변경 시 필수).

```
/inspect-abp → 처방
  ↓
[자동] py scripts/abp_backup.py backup <asset> <label>
  ↓
/tune-abp → 변경 적용
  ↓
검증 실패 시:  py scripts/abp_backup.py restore <asset> <label> --apply
  ↓
재dump 로 before/after 비교
```

## How to apply
- 사용자가 `/tune-abp` 호출 시 메인 에이전트가 backup 한 줄 자동 실행 후 그 path 를 Tuner prompt 에 포함
- 사용자가 직접 `set_cdo_property` / `batch_execute` 류 호출할 때도 같은 패턴 권장
- 매주 `prune --days 14` 1회로 디스크 정리

## 한계 명시
- Monolith 자체 한계 ([[reference-monolith-animgraph-editing-limits]]) 는 백업으로 우회 안 됨 (한계 그대로)
- save_asset P4 잠금 시 백업은 디스크 보존, 복원 시도도 동일 잠금 만나면 사용자 Ctrl+S 필요

관련 메모리: [[reference-monolith-animgraph-editing-limits]], [[reference-animgraph-node-editing]], [[project-pc01-psd-gmt-continuing-bias]].
