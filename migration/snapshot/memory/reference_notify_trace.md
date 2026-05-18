---
name: reference-notify-trace
description: Phase 6 (2026-05-18) — AnimNotify trace 채널. ABP 미수정. log_filter --notify + context_injector NOTIFY_TRACE 슬라이스. UE 콘솔 verbose 활성화 가이드 포함.
metadata: 
  node_type: memory
  type: reference
  originSessionId: 9dcc5175-e415-47ad-96d0-959bb0242e16
---

# Phase 6 — [NOTIFY_TRACE] AnimNotify trace

ABP 그래프 수정 회피 (Phase 5 thread safety 트라우마). 대신 UE 의 LogAnimNotify / LogAnimMontage / LogAnimation 카테고리를 verbose 로 활성화해서 자동 캡처.

## Verbose 활성화 (PIE 시작 후 UE 콘솔)

```
Log LogAnimNotify Verbose
Log LogAnimMontage Verbose
Log LogAnimation Verbose
```

또는 `Saved/Config/Windows/Engine.ini` (또는 DefaultEngine.ini) `[Core.Log]` 섹션:

```ini
[Core.Log]
LogAnimNotify=Verbose
LogAnimMontage=Verbose
```

## CLI 사용

```bash
# Notify 카테고리 자동 선택 + Notify/Montage 키워드 grep
python scripts/log_filter.py --notify --format std --tail 100

# 특정 PIE 세션의 Notify 만
python scripts/log_filter.py --notify --pie 58 --format std
```

## context_injector

`fetch_notify_trace_slice()` 가 두 단계로 캡처:

1. **Explicit [NOTIFY_TRACE]** — ABP/NotifyState BP 에 [NOTIFY_TRACE] PrintText 가 명시적으로 있으면 그것만
2. **UE 카테고리 fallback** — LogAnimNotify/LogAnimMontage/LogAnimation 중 "Notify|Montage|Section|Branching" 키워드 포함 라인

자동 std prefix 적용 (`[PIE=N frame=X t=T.TTTs]`).

## 명시적 채널 추가 (옵션, 위험)

원하면 NotifyState BP class (PC_01 의 `BP_NotifyState_EarlyTransition` 같은 것) 의 `Received_NotifyBegin` / `Received_NotifyEnd` 에 PrintText 추가:

```
[NOTIFY_TRACE] notify=EarlyTransition phase=Begin/End anim=<MontageName>
```

단, AnimNotify BP 의 호출 컨텍스트가 game thread 임을 사전 확인. Anim work thread 면 thread violation → crash 위험.

## 관련

- Phase 5 영구 포기: [[reference-log-pie-std-prefix]] — AnimGraph thread safety 제약
- Phase 1 std prefix: [[reference-log-pie-std-prefix]]
- GASP EarlyTransition: [[reference-gasp-early-transition]]
