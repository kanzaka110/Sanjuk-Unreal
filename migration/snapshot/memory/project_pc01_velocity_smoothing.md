---
name: pc-01-velocity-smoothing-phase-1a
description: "패드 아날로그 입력 노이즈로 인한 모션 진동(짧은 클립 끼임, 매칭 진동)을 해결하기 위한 Velocity 평활화 시스템. Phase 1A는 변수 + 갱신 로직 + ANIM_REC 디버그 출력까지. 입력 변수 교체 (IsStarting B 트리거 PrevVel 등)는 Phase 1A 본격 적용 단계로 분리."
metadata: 
  node_type: memory
  type: project
  date: 2026-05-13
  asset: /Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP
  originSessionId: e020acca-fb98-4cf6-963d-1d987445e1bd
---

## 배경

- 사용자 호소: 패드 입력 시 모션 간 노이즈 (짧은 클립 끼임 / 매칭 진동)
- 진단: 패드 아날로그 미세 변동이 매 틱 임계 근처에서 진동 → Chooser/IsStarting 등 모든 시스템에 전파
- 처방: Velocity 평활화 후 그 값을 입력 변수로 교체

## Phase 1A — 변수 + 관찰 단계 (2026-05-13 완료)

### 변수 2개 추가 (PC_01_ABP)

| 변수 | 타입 | 카테고리 | default | IE |
|---|---|---|---|---|
| `SmoothedVelocity` | struct:Vector | Buffer | (0,0,0) | false |
| `VelocityInterpSpeed` | double | Essential Values | 8.0 | true |

### UpdateVariables 그래프 갱신 노드 (6개 추가, 6개 연결)

식: `SmoothedVelocity = VInterpTo(SmoothedVelocity, Velocity, DeltaTime, VelocityInterpSpeed)`

배치 위치: `Set NoneZeroVelocity` (K2Node_VariableSet_62, pos [3136,16]) 의 `then` 핀이 비어있었기 때문에 그 뒤에 chain.

노드 ID:
- `K2Node_VariableGet_8` — Get SmoothedVelocity (Current)
- `K2Node_VariableGet_51` — Get Velocity (Target)
- `K2Node_VariableGet_53` — Get Delta Time
- `K2Node_VariableGet_54` — Get VelocityInterpSpeed
- `K2Node_CallFunction_30` — VInterpTo (KismetMathLibrary)
- `K2Node_VariableSet_24` — Set SmoothedVelocity

exec: VarSet_62.then → VarSet_24.execute  
data: 4 Get → VInterpTo (Current/Target/DeltaTime/InterpSpeed) → VarSet_24.SmoothedVelocity

### AnimRewindRecorderEmit (ANIM_REC) 노드 3개 추가 — **미완**

- `K2Node_FormatText_3` — 신규 FT. Format 텍스트 `{prev},"svl"={svl}` 설정됨 (default_value 직렬화는 OK)
- `K2Node_VariableGet_28` — Get SmoothedVelocity
- `K2Node_CallFunction_5` — VSizeXY (Vector Length XY)

연결 완료:
- Get SmoothedVelocity (Get_28) → VSizeXY (Func_5.A)

연결 **미완** (Monolith 한계):
- FT_3 의 argument pin (prev, svl) 이 컴파일 후에도 미생성
- K2Node_FormatText의 Format 텍스트 변경 → argument pin 자동 재생성은 K2Node 내부 `ReconstructNode`/`SyncArgumentPins` 트리거 필요. Monolith `set_pin_default` 만으로는 트리거 안 됨
- 따라서 svl/prev 연결 + FT_0.Result→FT_3.prev / FT_3.Result→FT_5.Format 재배선 불가
- 결과: 현 상태에서 ANIM_REC 라인에 svl 출력 안 됨. 사용자가 에디터에서 FT_3 노드 선택 → Format 텍스트 박스 클릭 → Enter (또는 동일 내용 재입력) 하면 pin 갱신될 가능성. 그 후 수동으로 prev/svl 연결 및 chain 재배선.

대안 권장: ANIM_REC 디버그는 별도 가이드 작업이 더 안정적. UpdateVariables 의 SmoothedVelocity 계산은 정상 작동하므로 PIE 검증에는 영향 없음.

### 컴파일 / 저장

- compile_blueprint — success, errors=0, warnings=0 (2회 모두)
- save_asset — Failed (P4 잠금, 메모리 reference 대로 예상된 결과). 사용자 Ctrl+S 필요.

## Phase 1A 본격 적용 후보 (다음 단계)

평활화된 SmoothedVelocity 를 입력 변수로 교체:

1. **IsStarting B 트리거** — `bPrevIsStart` latch 패턴 (reference_pc01_isstarting_design.md 참조). PrevVel 비교에 SmoothedVelocity 사용
2. **Chooser 평가 입력** — Speed2D 계산을 `VSizeXY(SmoothedVelocity)` 로 교체 (현재는 Velocity 직접)
3. **CircleStrafeHysteresis** — Velocity 기반 측면 판정 (project_pc01_circle_strafe_hysteresis.md)
4. **OnStateEntry trigger 조건** — Speed 임계 비교에 SmoothedVelocity 사용
5. **PrevVelocity buffer** — 현재 PrevVelocity는 Velocity 그대로. SmoothedVelocity 도입 후 PrevSmoothedVelocity 별도 추가 검토

각 적용 단계마다 별도 처방 + Inspector 호출 권장. 한 번에 다 교체 X.

## PIE 검증 시나리오 (Phase 1A)

ANIM_REC svl 출력이 미완이므로, **임시 ShowDebug 또는 Print String 노드**로 SmoothedVelocity 값 직접 확인 가능:

1. 패드 정지 → 천천히 가속 → 멈춤
   - 기대: `Speed2D` (현재 ANIM_REC `sp`) 는 빠르게 따라가고 `VSizeXY(SmoothedVelocity)` 는 약 0.1~0.3초 지연
2. 키보드 정지 → 이동 → 멈춤
   - 기대: 둘이 거의 같음 (디지털 입력은 본래 끊김 없음)
3. VelocityInterpSpeed 값 변경 (8 → 4: 더 부드럽게 / 8 → 16: 더 빠르게)
   - Essential Values 카테고리, instance_editable=true 이므로 details 패널에서 즉시 튜닝

## 파일 위치

- 사전 dump: `C:\Dev\Sanjuk-Unreal\Saved\phase1a_*.json`
- 사후 dump: `C:\Dev\Sanjuk-Unreal\Saved\phase1a_post_*.json`

## 알려진 함정

- **K2Node_FormatText argument pin 자동 생성 미동작** (Monolith 한계): set_pin_default 로 Format 텍스트 변경해도 prev/svl 등 인자 핀 생성 안 됨. compile_blueprint 후에도 동일. 우회: 사용자 수동 노드 갱신 또는 처음부터 핀 슬롯 있는 기존 FT 노드 수정 (위험)
- **VSize2D vs VSizeXY**: Vector(struct:Vector) 입력엔 `VSizeXY`. `VSize2D` 는 Vector2D 입력용. 기존 FT_8 chain 에서 vlen은 VSizeXY 사용 중

## How to apply

- 다음 세션에서 Phase 1A 본격 적용 시작 시 이 메모리 참조
- IsStarting/Chooser 등 SmoothedVelocity 교체 작업은 Inspector 처방 → Tuner 적용 순서
- ANIM_REC svl 출력 마무리는 사용자 수동 작업 필요 시 별도 가이드

## 2026-05-14 크래시 후 복원

이전 세션에서 크래시로 UpdateVariables 의 Velocity Smoothing 6노드 + 코멘트 + Set_62→체인 splice 가 유실. Inspector 정찰 후 복원 완료. 복원 범위는 **Phase 1A 본체(변수+갱신 노드+코멘트)만**. ANIM_REC svl 필드는 별도 단계로 미포함 (이전 메모리 §"AnimRewindRecorderEmit 미완" 그대로).

### 복원된 변수
- `VelocityInterpSpeed` (float, default 8.0, Category=`OrientWraping`, InstanceEditable=true) — 다시 추가됨
- (`SmoothedVelocity` 는 잔존하고 있어서 재추가 불요)

### 복원된 노드 ID (2026-05-14 신규)

| 역할 | 노드 ID | 자동 layout 후 pos |
|---|---|---|
| Get SmoothedVelocity | `K2Node_VariableGet_57` | 보존(코멘트 자동확장) |
| Get Velocity | `K2Node_VariableGet_58` | 동상 |
| Get Delta Time | `K2Node_VariableGet_59` | 동상 |
| Get VelocityInterpSpeed | `K2Node_VariableGet_60` | 동상 |
| VInterp To (KismetMathLibrary) | `K2Node_CallFunction_29` | [3870, 64] |
| Set SmoothedVelocity | `K2Node_VariableSet_73` | [4158, 16] |
| Comment "모션과 모션 사이 순간 노이즈 줄이기 위한 처리" | `EdGraphNode_Comment_30` | 888×614 auto-wrap |

(이전 세션 ID — Get_8/51/53/54/CallFunction_30/VariableSet_24 — 는 크래시 손실분. 본 복원 ID 가 현재 정본)

### Wire 6건 (모두 success)
- exec: `K2Node_VariableSet_62.then` (id `5A6D331740BB54224D333BA6F1FAF595`, Set NoneZeroVelocity 의 then 빈 핀) → `K2Node_VariableSet_73.execute`
- data: 4 Get → VInterpTo (Current/Target/DeltaTime/InterpSpeed)
- data: VInterpTo.ReturnValue → Set SmoothedVelocity.SmoothedVelocity

### 컴파일 / 저장
- `compile_blueprint` — success, status=UpToDate, errors=0, warnings=0
- `save_asset` — saved=true, was_dirty=true (이전 세션과 달리 P4 잠금 없이 자동 저장됨)

### 사후 덤프
- pre:  `C:\Dev\Sanjuk-Unreal\Saved\PROBE_UpdateVariables_pre_velocity_smoothing_restore_20260514.json` (2,190 bytes)
- post: `C:\Dev\Sanjuk-Unreal\Saved\PROBE_UpdateVariables_post_velocity_smoothing_restore_20260514.json` (172,093 bytes)

### Side effect 체크
- `K2Node_VariableSet_62` 의 다른 핀(execute from Branch_19, NoneZeroVelocity input from Get_73) 변경 없음
- `K2Node_IfThenElse_19`, `K2Node_ExecutionSequence_3` 등 기존 구조 무변
- ANIM_REC / AnimRewindRecorderEmit 그래프 무손 (의도대로 미작업)

### 다음 단계 (변경 없음)
이전 §"Phase 1A 본격 적용 후보" 그대로. IsStarting B 트리거 PrevVel 교체부터 시작 권장.
