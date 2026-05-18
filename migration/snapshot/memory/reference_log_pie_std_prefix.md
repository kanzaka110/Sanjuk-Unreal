---
name: reference-log-pie-std-prefix
description: "Phase 1 (2026-05-18) — UE 로그에 PIE 세션 감지 + 표준 prefix `[PIE=N frame=X t=T.TTTs]` 적용. log_filter.py + context_injector.py 양쪽 통합."
metadata: 
  node_type: memory
  type: reference
  originSessionId: 9dcc5175-e415-47ad-96d0-959bb0242e16
---

# Phase 1 — 메타 표준화 [PIE=N frame=X t=T.TTTs]

UE Output Log 의 매 라인에 PIE 세션 / 프레임 / 상대 시각이 통일된 prefix 로 표시되도록 가공. ABP 미수정 (안전).

## PIE 감지 마커

- **시작**: `LogWorld: Bringing World /.../UEDPIE_N_<map> up for play`
- **종료**: `LogWorld: BeginTearingDown for /.../UEDPIE_N_<map>`

SB2_2.log 1개에서 58 PIE 세션 감지 (2026-05-18). 한 번의 PIE 클릭이 3개 PIE 세션 (TestDLV → LobbyMap → COL_WP) 으로 분해됨.

## 사용법

### log_filter.py

```bash
# PIE 세션 리스트
python scripts/log_filter.py --list-pie

# ANIM_REC 라인 표준 prefix 출력
python scripts/log_filter.py --category LogBlueprintUserMessages \
    --grep "ANIM_REC" --format std --tail 50

# 특정 PIE 세션만
python scripts/log_filter.py --pie 58 --format std --tail 200
```

### context_injector.py

자동 std prefix 적용. 모든 로그 섹션 (ANIM_REC, SM_TRACE, NOTIFY_TRACE, UE log filter) 이 표준 prefix 로 출력.

```python
from scripts.lib.context_injector import build_context
ctx = build_context(case="...", log_lines=200)
# 출력 라인 형태: [PIE=58 frame= 361 t= 16.253s] [LogBlueprintUserMessages:] ...
```

## 출력 형태

원본:
```
[2026.05.18-04.49.18:830][667]LogBlueprintUserMessages: [PC_01_ABP_C_0] [ANIM_REC] "f"=308,667,...
```

std:
```
[PIE=58 frame=  667 t=  7.926s] [LogBlueprintUserMessages:] [PC_01_ABP_C_0] [ANIM_REC] "f"=308,667,...
```

## 구현 위치

- `scripts/log_filter.py` — `find_pie_sessions()`, `assign_pie()`, `std_prefix()`, CLI `--format std/--list-pie/--pie N`
- `scripts/lib/context_injector.py` — 동일 함수 sibling 복제, build_context 가 PIE sessions 1회 추출 후 모든 fetch_*_slice 에 전달

## 관련

- Phase 2 채널 E: [[reference-log-filter-py]] (생성 후 갱신)
- Phase 7 채널 L: [[project-pc01-anim-rec-unmapped-added]] context_injector.py
- Phase 5 영구 포기: AnimGraph thread safety — `as/ms/pwm/ist + pas/pms2/ppwm` Prev 필드 조합으로 SM state 유추
