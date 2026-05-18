---
name: PC_01 HasEvade 파이프라인 + Chooser 적용 작업 진행
description: HasEvade 변수 구조, RuleMoveFlag PropertyAccess, 4개 Chooser 적용 현황 (2026-05-11 갱신)
type: project
originSessionId: 52fcc70d-c480-47be-be56-421b47dea3e8
---
## HasEvade 파이프라인 (T3D 실측 확정, 2026-05-11)

### 변수 (PC_01_ABP 자체)
- `RuleMoveFlag` (FName) — 카테고리 `디폴트`
- `PrevRuleMoveFlag` (FName) — 카테고리 `디폴트`
- `HasEvade` (bool) — 카테고리 `Evade`
- `HasEvadeChanged` (bool) — 카테고리 `Evade`, edge detect 결과
- `HasEvadeDuration` (real)
- `EvadeDurationThreshold` (real)
- `PrevHasEvade` (bool) — **메모리 정정**: 이름 `bPrevHasEvade` 아님. 이미 edge detect 로직 완성됨
- `AirEvade` (bool) — 카테고리 `디폴트`

### RuleMoveFlag setter 출처 (확정)
- **K2Node_PropertyAccess** (UE Property Access binding, ThreadSafe)
  - Path(0)="GetRuleMoveFlag", ResolvedPinType=(PinCategory="name")
  - 부모 클래스 `SBActorAnimInstance` (SB2 C++)의 함수 호출
- `EAnimPropertyAccessCallSite.WorkerThread_Unbatched`로 worker thread에서 AnimGraph 평가 직전 호출 (캐시)
- 즉 라이브 갱신 지연 원인은 PropertyAccess 자체가 아니라 부모 C++ `GetRuleMoveFlag()` 본문의 데이터 소스에 달림

### UpdateVariables 흐름 (T3D K2Node 실측)
```
ExecutionSequence → Knot
  ├ Set PrevRuleMoveFlag = (Get RuleMoveFlag)         # 이전값 백업
  └ Set RuleMoveFlag = K2Node_PropertyAccess (GetRuleMoveFlag())
  ├ IfThenElse_2:
  │   조건: (PrevRuleMoveFlag=="Evade" OR PrevRuleMoveFlag=="AirEvade")
  │         AND (PrevRuleMoveFlag != RuleMoveFlag)    # 회피 진입 검출
  │   TRUE  → HasEvadeDuration=EvadeDurationThreshold, HasEvade=true
  │   FALSE → IfThenElse_5: HasEvadeDuration<=0
  │            TRUE  → HasEvade=false, AirEvade=false
  │            FALSE → HasEvadeDuration = FClamp(HasEvadeDuration - DeltaTime, 0, Threshold)
  ├ Set HasEvadeChanged = NotEqual(HasEvade, PrevHasEvade)   # edge detect
  ├ Set PrevHasEvade = HasEvade
  └ IfThenElse_4 (PrevRuleMoveFlag=="AirEvade") → Set AirEvade=true
```

## Chooser 적용 현황 (2026-05-11 grep 실측)

PC_01 Chooser 4개 (state machine 라우팅 대체):

| Chooser | 크기 | HasEvade | HasEvadeChanged | AirEvade | 상태 |
|---|---|---|---|---|---|
| `/PC_01/StateMachine/GroundMoving` | 715KB | ✅ | ✅ | ✅ | **완료** (오늘 본인 작업) |
| `/PC_01/StateMachine/GroundIdle` | 190KB | ❌ | ❌ | ❌ | **미작업** |
| `/PC_01/StateMachine/Falling` | 38KB | ❌ | ❌ | ❌ | **미작업** |
| `/PC_01/StateMachine/EvieAnimChooser_StateMachine` (Router) | 18KB | ❌ | ❌ | ❌ | **미작업** |

### GroundMoving 글로벌 컬럼 (templates)
`;StateMachineMoveState;AnimStance;PrevMovementMode;OverlayPoseState;HasEvadeChanged;TrjIsCircling;InWriggle;WriggleEnd;`

회피 회복 클립이 결과로 매핑됨:
- `P_Player_Fist_Battle_*_StartAfterEvade_*` (Jog/Walk/Sprint 모두)
- `P_Player_*_Start_F_*_Evade`
- `P_Player_Fist_Air_*_Evade01_E_*` (Walk/Jog/Run/Sprint)

## 다음 액션 (재개 시 시작점)

1. **Falling Chooser**: AirEvade 컬럼 + 공중 회피 클립 row 추가 (가장 작은 에셋, 파일럿 적합)
2. **GroundIdle Chooser**: HasEvade 컬럼 + 제자리 회피 row 추가
3. **EvieAnimChooser_StateMachine (Router)**: 상위 라우터에 회피 전용 분기 검토

작업 방법:
- Monolith는 ChooserTable 편집 액션 없음. PythonScriptPlugin도 SB2에서 비활성.
- → **UE 에디터에서 직접**: GroundMoving Chooser 열어서 HasEvade/HasEvadeChanged/AirEvade 컬럼 binding 패턴 확인 후 대상 Chooser에 동일 컬럼 Add → row 매치값 설정

## Why
회피 이벤트 Chooser 적용은 PC_01 회피 후속 동작(StartAfterEvade)의 표준화 경로. GroundMoving 완료가 templates가 됨.

## How to apply
- 재개 시: Falling부터 (작고 단순)
- 메모리 stale 검증: Chooser 인덱싱 일자 확인 (2026-05-11 이후 변경 시 재grep)
- 변수명 주의: `PrevHasEvade` (b prefix 없음)

## 관련 메모리
- `project_pc01_chooser_evaluation.md` — Chooser enter-time 평가 ground truth
- `project_pc01_abp_chain.md` — ABP 체인 22노드 구조
- `reference_monolith_animgraph_editing_limits.md` — Chooser ResultsStructs protected
