# 청소 작업 결과 (2026-05-19 후속)

분리 작업 후 dead 함수/변수 제거.

## 제거 항목

### AM_SBFootSyncNotifies (Sync — 신규)

| 종류 | 이름 | 제거 사유 |
|---|---|---|
| 함수 | `SetMoveType` (43 노드) | 호출자 0 — Task #4에서 ProcessFoot 호출 제거 후 dead |
| 함수 | `SetFootStepSetKey` (102 노드) | 호출자 0 — 동일 |
| 변수 | `FootStepSetKey` (byte enum) | 31 참조 모두 SetFootStepSetKey 내부 → 함수 제거 시 dead |
| 변수 | `StepInSpeedThreshold` (double) | 참조 0 (원래 "Nouse" 카테고리) |

### AM_SBFootStepNotifies (Step — 기존)

| 종류 | 이름 | 제거 사유 |
|---|---|---|
| 변수 | `StepInSpeedThreshold` (double) | 참조 0 — 분리 무관, 원래 항상 미사용 |

## 보존 항목 (제거 후보였으나 ProcessFoot에서 활성 사용)

Sync에서 다음 변수들은 FX/Sound 의미가 있지만 ProcessFoot의 state/branch 로직에 여전히 참조되어 보존:

- `MoveType` — ProcessFoot 2 Read (default 값으로 동작)
- `FootSoundType` — ProcessFoot 12 Set/Get
- `IsScuffing` / `PrevIsScuffing` — 12 참조 (state tracking)
- `ScuffThreshold` / `UseScuff` — config read
- `JumpSpeedThreshold` / `LandSpeedThreshold` — config read
- `UseStepOut` / `StepOutOffset` — IsFootOnGround / ProcessFoot config

이들을 제거하려면 ProcessFoot 그래프 재구성이 필요해 위험도 높음. 별도 청소 패스 사양.

## 최종 비교 (Step vs Sync)

| 그래프 / 변수 | Step | Sync | Delta |
|---|---:|---:|---:|
| Variables | 42 (`-StepInSpeedThreshold`) | **40** | -1 (Step) / -2 (Sync) |
| Functions | 9 | **7** (`-SetMoveType`, `-SetFootStepSetKey`) | -2 |
| EventGraph | 6 | 6 | 0 |
| ApplyModifier | 83 | 83 | 0 |
| ProcessFoot | 291 | 287 | -4 |
| RevertModifier | 5 | 5 | 0 (함수 교체) |
| AddNotify | 18 | **11** | -7 (실 로직 8 + 자동 Knot 3) |
| GetPeakSocketSpeed | 70 | 70 | 0 |
| GetPeakBoneSpeed | 62 | 62 | 0 |
| IsFootOnGround | 10 | 10 | 0 |

## 검증

- ✅ Sync 컴파일: 0 error, 0 warning
- ✅ Sync 저장: was_dirty → saved
- ✅ Step 컴파일: 0 error, 0 warning
- ✅ Step 저장: was_dirty → saved
- ✅ compare_blueprints: 의도된 diff만 (variables 1 modified + 1 removed, functions 2 removed, graphs 2 removed)

## AddNotify 11노드 내역 (Sync)

실 로직 8 + UE 자동 라우팅 Knot 3:
- 실 로직: FunctionEntry, Branch(IfThenElse), Get IsLeftSide, 2× AddAnimationSyncMarker, Clamp, Get FootDefinition, Get Animation Sequence
- 자동 Knot: K2Node_Knot_4, K2Node_Knot_5, K2Node_Knot_6 (변수/함수 제거 후 UE save가 라우팅 정리용 삽입)

Knot 노드는 컴파일 영향 없음 — 무해.

## 향후 청소 패스 (옵션, 별도 작업)

Sync에서 더 공격적 청소가 필요하면:
1. `ProcessFoot`의 FX/Sound state 로직 (FootSoundType, IsScuffing 분기) 제거
2. 의존 변수 (MoveType, FootSoundType, scuff/jump/land 임계값) 제거
3. SetMoveType/SetFootStepSetKey 제거된 슬롯 — 호출 종속 제거된 점에서 추가 청소 가능

위험도가 높아 ProcessFoot 전체 흐름 분석 필요. 현 시점 보류 권장.
