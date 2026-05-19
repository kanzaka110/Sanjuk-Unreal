# AnimModifier 분리 작업 결과 (2026-05-19)

## 작업 요약

`AM_SBFootSyncNotifies` (기존 `AM_SBFootStepNotifies` 의 100% 복제본) → **Sync Marker 전용 모디파이어로 변경 완료**.

## Compare Result (vs AM_SBFootStepNotifies)

| 항목 | Step (기존) | Sync (변경) | Delta |
|---|---:|---:|---:|
| Variables | 42 | 42 | 0 (변수 구조 동일) |
| Functions | 9 | 9 | 0 |
| **NotifyTimeOffset** | **-0.09** | **0.0** | ✅ |
| EventGraph | 6 | 6 | 0 |
| ApplyModifier | 83 | 83 | 0 |
| **ProcessFoot** | **291** | **287** | **-4** ✅ (SetMoveType x2 + SetFootStepSetKey x2 제거) |
| RevertModifier | 5 | 5 | 0 (1 added, 1 removed — 함수 교체) |
| **AddNotify** | **18** | **8** | **-10** ✅ (AddNotifyEvent → AddSyncMarker × 2) |
| SetMoveType (함수 자체) | 43 | 43 | 0 (호출만 제거, 함수 body 유지) |
| SetFootStepSetKey (함수 자체) | 102 | 102 | 0 (동일) |
| GetPeakSocketSpeed | 70 | 70 | 0 |
| GetPeakBoneSpeed | 62 | 62 | 0 |
| IsFootOnGround | 10 | 10 | 0 |

## 변경 상세

### AddNotify (18 → 8 노드)

**Before**: AddAnimationNotifyEvent → DynamicCast(AN_SBFootStepNotify) → 4 VariableSet (SocketName/Volume/Pitch/FootStepSetKey)

**After**: Branch(IsLeftSide) → AddAnimationSyncMarker × 2 (MarkerName: "Foot_L" / "Foot_R")

남은 8 노드:
1. K2Node_FunctionEntry_0 (AddNotify)
2. K2Node_IfThenElse_0 (Branch — IsLeftSide condition)
3. K2Node_VariableGet_4 (Get IsLeftSide)
4. K2Node_CallFunction_1 (AddAnimationSyncMarker, MarkerName="Foot_L")
5. K2Node_CallFunction_2 (AddAnimationSyncMarker, MarkerName="Foot_R")
6. K2Node_CallFunction_0 (Clamp 0~10000 — 기존)
7. K2Node_VariableGet_2 (Get FootDefinition — NotifyTrack pin)
8. K2Node_VariableGet_20 (Get Animation Sequence)

### RevertModifier (5 노드, 함수 교체)

- `RemoveAnimationNotifyTrack` → `RemoveAnimationSyncMarkersByTrack`
- ForEach loop 구조 유지 (FeetDefinition 순회)
- 결과: NotifyTrack 전체 삭제 대신 해당 트랙의 sync marker만 제거 — FX 모디파이어와 공존 가능

### ProcessFoot — SetMoveType/SetFootStepSetKey 호출 4건 제거 (291 → 287)

위치 2쌍에서 SetMoveType + SetFootStepSetKey 연속 호출 제거:
- **Pair 1** (10640, 4160): K2Node_Knot_10 → ~~CF_34 (SetMoveType)~~ → ~~CF_35 (SetFootStepSetKey)~~ → CF_18
  - 결과: K2Node_Knot_10 → K2Node_CallFunction_18 직결
- **Pair 2** (8624, 1744): K2Node_Knot_18 → ~~CF_29 (SetMoveType)~~ → ~~CF_32 (SetFootStepSetKey)~~ → CF_26
  - 결과: K2Node_Knot_18 → K2Node_CallFunction_26 직결

SetMoveType / SetFootStepSetKey **함수 자체**는 그대로 (43/102 노드). Step 모디파이어에서 여전히 사용 가능.

### CDO

- NotifyTimeOffset: -0.09 → **0.0** (정확한 접지 순간)

## 검증

- ✅ compile_blueprint: success, 0 errors, 0 warnings
- ✅ save_asset: success (was_dirty=true → 디스크 반영)
- ✅ compare_blueprints (vs Step): 의도된 변경만 (variables 1, graphs 3)

## 컨벤션 / 사실 확인

- **SB2 Sync Marker 이름**: `Foot_L` / `Foot_R` — PC_01_Body_001_Skeleton.uasset binary에서 확인 (UE 표준 Lyra/GASP 컨벤션)
- **NotifyTrack 사용**: Sync도 `FootDefinition.NotifyTrack` ("Footstep Left/Right") 재사용 — Step의 FX 노티파이와 같은 트랙에 마커 배치
- **Sync 마커 제거 함수**: `RemoveAnimationSyncMarkersByTrack` (track 단위) — FX 노티파이 영향 없음

## 다음 단계 (별도 작업)

1. **PC_01 Run 시퀀스 일괄 Apply** — `AM_SBFootSyncNotifies` 를 비전투 Run start/loop 시퀀스에 일괄 적용
   - 위치: `/Game/Art/Character/PC/PC_01/Animation/Body/Run/`
   - 우선순위: Run_Loop_F, Run_Loop_FL/FR/BL/BR/B/LL/LR/RL/RR, Run_Start_F_L/Rfoot
2. **PIE 검증** — Run Start → Loop 사이클 꼬임 해소 여부 확인
   - 진단 보고서 [[pc01-mm-pipeline]] 의 BlendStack DoNotSync + cardinality=1 조합과 함께 검증 필요
3. **Skeleton 등록** — `PC_01_Body_001_Skeleton` 에 `AM_SBFootSyncNotifies` 추가 등록 (신규 시퀀스 자동 후보화)

## 롤백 (필요 시)

- P4: 작업 전 체크아웃 했다면 `p4 revert /Game/Art/TA/AnimModifiers/AM_SBFootSyncNotifies.uasset`
- 또는 git checkout (Sanjuk-Unreal 레포는 .uasset 미포함이므로 SB2 워크스페이스에서 처리)
- MCP 재작업: `00_README.md` + `01_addnotify_before.md` + `02_revertmodifier_before.md` 의 노드 인벤토리 참고
