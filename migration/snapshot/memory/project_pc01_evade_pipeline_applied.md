---
name: PC_01 회피 파이프라인 ABP 적용 완료 (2026-05-15)
description: reference_pc01_evade_pipeline_design 설계 중 EvadeDurationThreshold 및 UMSB OR 게이트 부분을 PC_01_ABP에 실제 적용한 변경 이력.
type: project
originSessionId: tuner-20260515
---

## 적용 일자
2026-05-15

## 적용 항목

### 1. EvadeDurationThreshold default 변경
- 에셋: `/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP`
- 변수: `EvadeDurationThreshold` (double, Category=Evade)
- 변경: **0.05 → 0.3**
- 방법: `blueprint_query.set_variable_defaults`

### 2. UpdateMovementStateWithBuffer OR 게이트에 HasEvade 추가
- 그래프: `UpdateMovementStateWithBuffer`
- 추가 노드:
  - `K2Node_VariableGet_4` = Get HasEvade (pos 3380,160)
  - `K2Node_CallFunction_0` = OR Boolean (BooleanOR, pos 3536,200) — 처방서의 OR_NEW
- 결선 변경:
  - 제거: `OR_0.ReturnValue → Select_2.Index` (기존 직결)
  - 추가:
    - `VG_HE.HasEvade → OR_NEW.A`
    - `OR_0.ReturnValue → OR_NEW.B`
    - `OR_NEW.ReturnValue → Select_2.Index`
- 효과: `Select_2.Index = IsMoving() OR HasEvade OR (RuleMoveFlag=="Evade" OR =="AirEvade")`

## 노드 ID 매핑 (post-적용)
- `K2Node_CommutativeAssociativeBinaryOperator_0` — OR_0 (IsMoving / RuleMoveFlag OR 결과)
- `K2Node_CommutativeAssociativeBinaryOperator_1` — OR_1 (RuleMoveFlag=="Evade" OR =="AirEvade")
- `K2Node_CallFunction_0` — OR_NEW (HasEvade OR OR_0)
- `K2Node_VariableGet_4` — Get HasEvade
- `K2Node_Select_2` — CandidateMovementState selector
- `K2Node_PromotableOperator_3` — Equal (RuleMoveFlag, "Evade")
- `K2Node_PromotableOperator_2` — Equal (RuleMoveFlag, "AirEvade")

## 검증
- compile_blueprint: success, status=UpToDate, 0 errors, 0 warnings
- validate_blueprint: 0 errors, 0 warnings
- save_asset: saved=true, was_dirty=true (P4 잠금 없이 저장 성공)
- diff (pre→post): +3 결선, -1 결선 — 정확히 처방대로
- side-effect: 0 (다른 결선 무손상)

## 백업
- pre-dump:
  - `C:/Dev/Sanjuk-Unreal/Saved/Logs/hasevade_restore/umsb_pre_20260515.json`
  - `C:/Dev/Sanjuk-Unreal/Saved/Logs/hasevade_restore/vars_pre_20260515.json`
- post-dump:
  - `C:/Dev/Sanjuk-Unreal/Saved/Logs/hasevade_restore/umsb_post_20260515.json`
  - `C:/Dev/Sanjuk-Unreal/Saved/Logs/hasevade_restore/vars_post_20260515.json`

## 함정/팁
- `add_nodes_bulk` 에서 `node_type=K2Node_CommutativeAssociativeBinaryOperator` 로 BooleanOR 노드를 만들면 함수 미할당 빈 노드가 생성됨 (핀 0개, title "None"). **반드시 `node_type=CallFunction` + `function_name=BooleanOR` + `target_class=/Script/Engine.KismetMathLibrary`** 로 추가해야 정상 핀 (A/B/ReturnValue) 생성.
  - 결과 노드 클래스는 `K2Node_CallFunction` 이지만, 컴파일러는 이를 기존 `K2Node_CommutativeAssociativeBinaryOperator` 와 동일하게 처리 (양쪽 모두 KismetMathLibrary::BooleanOR 호출).
- `disconnect_pins` 파라미터는 `source_*` 가 아니라 `node_id` + `pin_name` + (선택) `target_node` + `target_pin`.
- `set_variable_defaults` 파라미터는 `variable_name` 가 아니라 `name`.

## How to apply
- 이 패턴 후속 작업 시 `project_pc01_hasevade_pipeline.md` (bPrevHasEvade 셋업 등 잔존 작업) 참조.
- 회피 후 끼어듦 추가 호소 시: ANIM_REC 로그 확인 → 다른 갱신 함수에도 HasEvade 게이트 추가 가능.
