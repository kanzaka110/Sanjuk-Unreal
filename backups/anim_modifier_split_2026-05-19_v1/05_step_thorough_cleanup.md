# Step + Sync 전수 dead 청소 결과 (2026-05-19 추가)

이전 청소 작업이 Sync 위주였음. Step 전수 검사 후 dead 항목 추가 제거.

## 분석 방법

- 9 함수 모두 search_nodes로 호출자 검사 → ApplyModifier/RevertModifier(entry) + 7 비-entry 모두 호출 확인 → **함수 제거 0**
- 41 변수 모두 search_nodes로 Read/Write 검사 → 0참조 또는 write-only 식별

## 발견된 dead 변수 (Step + Sync 양쪽 동일)

| 변수 | 상태 | 제거 결정 |
|---|---|---|
| `IsZeroFrame` | 참조 0 | ✅ 변수만 제거 |
| `CurrVFootSpeed` | Set 1개, Get 0 (write-only) | ✅ Set 노드 제거 + 변수 제거 |
| `CurrVRootSpeed` | Set 1개, Get 0 (write-only) | ✅ 동일 |
| `PostVRootSpeed` | Set 1개, Get 0 (write-only) | ✅ 동일 |

## 제거 대상 노드 (ProcessFoot)

| 노드 ID | 위치 | exec 컨텍스트 | 안전성 |
|---|---|---|---|
| K2Node_VariableSet_21 (Set CurrVFootSpeed) | 12544, 4688 | Knot_11 → terminal | terminal, 안전 |
| K2Node_VariableSet_35 (Set CurrVRootSpeed) | 14608, 4688 | Knot_9 → terminal | terminal, 안전 |
| K2Node_VariableSet_33 (Set PostVRootSpeed) | 13568, 4688 | Knot_34 → 자기 → Knot_9 → Set_35 | chain 양쪽 함께 제거 → 자연 dead-end |

Knot 잔존 (Knot_9 등) 은 무해 — 컴파일 0 warning 확인.

## 보존된 dead 후보 변수 (Step + Sync — 더 검토 필요)

다음은 사용 중이거나 위험도 높아 보존:

| 변수 | Step 상태 | 비고 |
|---|---|---|
| `UseBipedNotifyOnly` | 1 read (SetFootStepSetKey) | Step에서만 사용 — Sync에선 SetFootStepSetKey 제거됨 → Sync에선 dead 가능. 추가 청소 패스 후보 |
| `PrevIsFootOnGround` | IsFootOnGround/ProcessFoot에서 활성 | 유지 |
| `IsFalling` | ProcessFoot 2 (Set/Get) | 유지 |

`UseBipedNotifyOnly` 는 Sync에서 dead 가능성 있음. 별도 패스에서 제거 검토.

## 최종 두 모디파이어 비교

| 항목 | Step | Sync | Delta |
|---|---:|---:|---:|
| Variables | 37 | **36** | -1 (Sync: FootStepSetKey 제거) |
| Functions | 9 | **7** | -2 (Sync: SetMoveType, SetFootStepSetKey 제거) |
| EventGraph 노드 | 6 | 6 | 0 |
| ApplyModifier | 83 | 83 | 0 |
| ProcessFoot | 288 (-3 from 291) | 284 (-3 from 287) | -4 |
| RevertModifier | 5 | 5 | 0 |
| AddNotify | 18 | 11 | -7 |
| GetPeakSocketSpeed | 70 | 70 | 0 |
| GetPeakBoneSpeed | 62 | 62 | 0 |
| IsFootOnGround | 10 | 10 | 0 |

## 총 청소 결과 (분리 작업 + 청소 합산)

원본 (분리 전) 기준:
- Step: 42 변수 / 9 함수 / 642 노드
- Sync: 42 변수 / 9 함수 / 642 노드 (Step 복제본)

분리+청소 후:
- Step: 37 변수 (-5) / 9 함수 / 639 노드 (-3 write-only Set)
- Sync: 36 변수 (-6) / 7 함수 (-2) / 484 노드 (-158: AddNotify -7, ProcessFoot -7, SetMoveType -43, SetFootStepSetKey -102, 그 외 +1 routing knot)

## 검증

- ✅ Step 컴파일: 0 error / 0 warning
- ✅ Sync 컴파일: 0 error / 0 warning  
- ✅ 양쪽 저장 (was_dirty → saved)
- ✅ 비교 diff: 의도된 분리 차이만 + 양쪽 동일 청소 효과
