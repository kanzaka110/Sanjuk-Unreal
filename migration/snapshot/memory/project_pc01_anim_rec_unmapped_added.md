---
name: project-pc01-anim-rec-unmapped-added
description: "2026-05-18 PC_01_ABP AnimRewindRecorderEmit 17필드 추가 (unmapped 13 + Chooser 5 - ow_a 중복제거). 기존 66 → 83 필드. dangling cleanup + 카테고리 순서 재배치."
metadata: 
  node_type: memory
  type: project
  originSessionId: 9dcc5175-e415-47ad-96d0-959bb0242e16
---

# 작업 요약 (2026-05-18)

PC_01_ABP `AnimRewindRecorderEmit` 그래프의 [ANIM_REC] 로그 라인에 unmapped ABP 변수 13개 신규 추가.

## 진행 흐름

1. **Phase 3a (fpa)** — `add_anim_rec_fpa_field.py` — `FootPlacementAlpha`
2. **Phase 3b (ow_a)** — `OverlayWeight`
3. **Phase 4 (ps_db)** — `CurrentSelectedDatabase` (GetDisplayName)
4. **Phase 3+ 일괄 (10필드)** — `scripts/add_anim_rec_10fields.py`

## 추가된 10필드 (Phase 3+)

| 약어 | 변수 | 타입 | 컨버터 |
|-----|------|------|--------|
| ptrd | PrevTargetRotationDelta | double | Conv_DoubleToString |
| tta | TrjTurnAngle | float | Conv_DoubleToString |
| hed | HasEvadeDuration | double | Conv_DoubleToString |
| sv | SmoothedVelocity | FVector | Conv_VectorToString |
| ise | bIsSprintEndTransition | bool | Conv_BoolToString |
| setr | SprintEndTransitionRemain | double | Conv_DoubleToString |
| seta | SprintEndTransitionDuration | double | Conv_DoubleToString |
| pas | PrevAnimStance | byte (enum) | Conv_ByteToString |
| pms2 | PrevMovementState | byte (enum) | Conv_ByteToString |
| ppwm | PrevPendingWalkMode | byte (enum) | Conv_ByteToString |

## 그래프 변경

- 노드 추가: 40개 (10필드 × 4노드)
- 신규 노드 ID: `K2Node_VariableGet_58..71`, `K2Node_CallFunction_59..100`
- 기존 chain tail `CF_40` → 새 chain (10단) → `CF_25 (Conv_StringToText)` 재배선
- compile success / 0 errors / 0 warnings
- save: saved=True (P4 잠금 우회됨)

## 패턴 (Concat_StrStr — FormatText pin auto-gen 한계 우회)

각 필드:
```
Get<Var> → Conv_<Type>ToString → s
prev_tail → Concat(A=prev_tail, B=' "abbr"=') → c1
c1 → Concat(A=c1, B=s) → c2  (= 새 tail)
```

## 중복 검증 보류

`fpa`/`ow_a`/`ps_db` 3필드는 기존 매핑 변수 중 같은 변수와 매핑됐을 가능성. PIE 후 라인에서:
- `ow` (ABP `OverlayWeight` 가능성) vs `ow_a` 비교
- `fpa` vs 기존 IK 관련 필드 비교

PIE 검증 미실시 (마지막 SB2.log는 신필드 추가 전 세션).

## Chooser 5필드 (Phase 3+++)

`scripts/add_anim_rec_chooser_fields.py` — Chooser 평가 결과 출력.

### 추가 구조

- 새 instance 변수 `__LastChooserOut` (struct: SBStateMachineChooserOut)
- `SetStateMachineBlendStackAnim` 그래프에 VariableSet `__LastChooserOut` 노드 추가 — EvaluateChooser2_0 결과를 instance var 에도 mirror set (기존 로컬 var `ChooserOutput` 와 동시)
- AnimRewindRecorderEmit 에 BreakStruct + Conv 5 + Concat 10 = ~17 노드 추가

### 5필드

| 약어 | 멤버 | 타입 |
|-----|------|------|
| ch_bp | BlendProfile | Name |
| ch_mm | UseMotionMatching | bool |
| ch_mmcl | MotionMatchingCostLimit | double |
| ch_bt | BlendTime | double |
| ch_st | StartTime | double |

### 한계

- **Tag (array<FName>) 포기**: monolith API 의 wildcard pin 추론 미지원. Array_Get / Array_Length 모두 컴파일 실패 ("타입이 결정되지 않았습니다"). 우회하려면 PC_01 ABP 안에 NameArrayToString utility 함수 신규 작성 필요.

## Dangling cleanup (2026-05-18 동일 세션)

`add_anim_rec_10fields.py` 첫 실행 부분 실패 + 재실행으로 chain 이중 발생.

- Live chain (살아있음): CF_15 → CF_23~CF_100 → CF_25
- Dangling chain (제거됨): CF_42~CF_82 + Conv 10 + VariableGet 10 = 40 노드

`scripts/cleanup_dangling_anim_rec_chain.py` 로 일괄 제거. CF_40.ReturnValue 분기 (CF_42, CF_61) 중 CF_42 분기 끊고 dangling 40 노드 remove_node.

## 카테고리 순서 재배치

`scripts/reorder_anim_rec_categories.py` — 8 wire 재배치로 출력 라인을 카테고리 순서로:

```
State Prev (pas → pms2 → ppwm)
→ State Sprint (ise → setr → seta)
→ IK (fpa)
→ Clip/MM DB (ps_db)
→ Motion (tta → ptrd → sv → hed)
→ Chooser (ch_bp → ch_mm → ch_mmcl → ch_bt → ch_st)
```

이전 시도 시 dangling chain 으로 매핑 오류 → 롤백 후 재실행 성공.

## ow_a 중복 제거 (2026-05-18 후속)

PIE 2464 라인 실측 분석 → `ow=0` 와 `ow_a=0.0` 100% 동일 분포 → **같은 OverlayWeight 변수**. 4노드 제거 (CF_27 lit, CF_28 val, CF_26 D2S, VG_32 OverlayWeight Get). CF_24 (fpa val) → CF_34 (ps_db lit) 직접 연결. compile 0 errors.

**최종 ANIM_REC 필드: 83**

## 후속 작업

- 사용자 PIE 검증 (83 필드 출력)
- Tag (ch_tag) 필요 시 utility 함수로 재시도
- FT_2~FT_11 안 흡수는 monolith FormatText pin auto-gen 한계로 영구 보류
- 조건부 제거 후보 (다른 PIE 시나리오 검증 후): mm/wt/rva/vac (변수 None 출력), ch_mmcl/ch_st (PIE 한정 상수)

## 관련

- 스크립트: `add_anim_rec_10fields.py` / `add_anim_rec_fpa_field.py` / `add_anim_rec_chooser_fields.py` / `cleanup_dangling_anim_rec_chain.py` / `reorder_anim_rec_categories.py`
- 기존 시스템: [[project-pc01-anim-rewind-recorder]] (66필드 baseline)
- 로그 필터: `scripts/log_filter.py` (Phase 2 + Phase 1 std prefix)
- Inspector context: `scripts/lib/context_injector.py` (Phase 7)
- Phase 1 std prefix: [[reference-log-pie-std-prefix]]
- Phase 5 영구 포기: AnimGraph thread safety
- Phase 6 NOTIFY_TRACE: [[reference-notify-trace]]
