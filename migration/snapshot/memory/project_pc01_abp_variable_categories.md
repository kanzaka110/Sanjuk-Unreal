# PC_01_ABP 변수 카테고리 정리

## 2026-05-15 미지정 28개 → 카테고리 일괄 지정

Inspector 진단 + 사용자 확정. `디폴트` 28개 → 0개. set_variable_defaults batch_execute (28/28 success).

### 카테고리 매핑 (28개)

| 카테고리 | 변수 |
|---|---|
| Trajectory (+6) | IsStrafe, TrjTurnAngle, TrjPastAngularVelocity, TrjCurrentAngularVelocity, TrjIsCircling, CircleStrafeHysteresis |
| Buffer (+8) | PrevIsStrafe, bPrevIsStart, PrevFullBodySlotWeight, PrevRuleMoveFlag, PrevAnimTag, PrevCircleStrafeHysteresis, PrevIsInTravel, PrevShouldWriggel |
| StateMachine (+6) | bIsStart, IsHeavyLand, JustLanded, RuleMoveFlag, CurrAnimTag, JustExitedSprint |
| Travel (+2) | ACTravelLogic, IsInTravel |
| Evade (+1) | AirEvade |
| Foot Placement (+1) | FootClampAlpha — 공백 있는 `Foot Placement` 다수파 쪽에 합류 (FootPlacement 단일은 별개 잔존) |
| Essential Values (+1) | SmoothedVelocity |
| AnimRewind (+1) | CurrentSequenceName |
| **Combat (신규, +2)** | IsGuarding, IsBattle |

### Combat 카테고리 (신규)

전투 상태/태세 관련 bool. 향후 attack/guard 류 추가 가능.

### 잔존 카테고리 중복 (이번 작업 범위 밖)

사용자가 "미지정 28개만 변경" 옵션 확정. 다음 후보:
- `Foot Placement` (9) ↔ `FootPlacement` (1) — 단일 1개를 다수파에 합치는 게 권장
- `Offset Root Bone` (2) ↔ `OffsetRootBone` (1)
- `OrientWraping` (2) ↔ `OrientationWarping` (1) — 사용자 오타 정리 + Epic 정식 표기
- `Trajectory` (11) ↔ `궤적` (1) — 한글 단일 → 영문 통합
- `StateMachine` (17) ↔ `States` (10) ↔ `상태` (5) — 의미 분리 여부 확인 필요

### 결과 검증
- 28/28 set_variable_defaults success
- compile errors=0, warnings=0
- default_value 보존 (28개 전체)
- side effect 0 (비대상 변수 변경 없음)
- save_asset 실패 (P4 잠금) → 사용자 Ctrl+S 또는 P4 체크아웃 후 저장 필요

### 백업
- pre: `C:/Dev/Sanjuk-Unreal/Saved/variables_pre_categorize_20260515.json`
- post: `C:/Dev/Sanjuk-Unreal/Saved/variables_post_categorize_20260515.json`
- batch result: `C:/Dev/Sanjuk-Unreal/Saved/batch_set_cat_result_20260515.json`
