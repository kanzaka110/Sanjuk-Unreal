---
name: PC_01 CircleStrafeHysteresis 메커니즘 + 갱신 한계
description: PC_01_ABP의 CircleStrafeHysteresis 계산식, Chooser 진입 조건, GroundMoving state에서 자동 갱신 안 되는 본질 원인.
type: project
originSessionId: 000356af-f6ab-4220-891c-ca3825b31e2a
---
## Hysteresis 원본 계산식 (UpdateVariables 그래프)
```
Hysteresis = |TrjTurnAngle| > SelectFloat(A=5, B=25, bPickA=PrevHysteresis)
           = (PrevHysteresis ? 5 : 25)  -- 진입 임계 25°, 유지 임계 5°
```

원본 trigger: `NotEqual(Hysteresis, PrevHysteresis)` → IfThenElse → SetStateMachineBlendStackAnim(bForceBlend=false, NewEnumerator1=GroundMoving)

## TrjTurnAngle 계산식 (Get_TrajectoryTurnAngle 함수)
```
TurnAngle = NormalizedDeltaRotator(
              VectorToRotator(TrjFutureVelocity),
              VectorToRotator(Velocity)
            ).Yaw
```
→ 미래 vs 현재 velocity yaw 차이.
**락온 상태에선 좌우 strafe와 회전 모두 큰 값** → trajectory feature만으로 두 케이스 분리 불가.

## TrjIsCircling 계산식
```
TrjIsCircling = (각속도 |Z| > 100°/s) AND (|TurnAngle| > 25°)
              -- TrjPastAngularVelocity.Z + TrjCurrentAngularVelocity.Z 사용
```

## Chooser N_LockOn_GroundMoving 진입 조건
마지막 2 row (28, 29) = Circle_Strafe row:
- PendingWalkMode = Jogging
- MoveSide = Enumerator2(L) / Enumerator4(R)
- **CircleStrafeHysteresis = MatchTrue**
- TrjTurnAngle FloatRange: row 28 [-180, -1], row 29 [1, 180]

## **결정적 한계 — 자동 갱신 안 됨의 본질**

`OnUpdate_GroundMoving` 함수 **존재하지 않음** (list_graphs 확인).

| State | OnStateEntry | OnUpdate | 결과 |
|-------|--------------|----------|------|
| TransitGroundMoving | ✓ | ✓ (단순 RInterpTo만, Chooser 호출 없음) | 빈번 transition 재진입으로 chooser 매 frame 평가 효과 |
| **GroundMoving** | ✓ | **✗ 없음** | OnStateEntry 1회만, Hysteresis 변해도 chooser 결과 안 갱신 |

→ GroundMoving state에 머무는 동안 Hysteresis 변화는 BlendStack에 반영 안 됨.

## **우회 해법 — Self-loop transition (사용자 구축, 유지 필수)**

GroundMoving → GroundMoving self-loop transition 존재. Rule = `Equal(CircleStrafeHysteresis, PrevCircleStrafeHysteresis)`.
**의도적 메커니즘**: Hysteresis 안정 상태에서 Equal=True → self-loop 발화 → OnStateEntry 재실행 → Chooser 재평가 → BlendStack 갱신.
이게 OnUpdate_GroundMoving 부재의 우회 해법. **삭제 금지.**

(과거 분석에서 "rule이 의도와 반대" "롤백 미완료"로 잘못 진단한 적 있음 — 2026-04-28 사용자 정정. 이 self-loop은 정상 baseline.)

## 시도했지만 모두 실패한 처방 (10+건)
1. SelectFloat 임계 5/15, 10/20, 8/30 등 임계 조정 — strafe noise 분리 못함
2. AND 게이트 + TrjIsCircling (임계 100→50→1→2→5) — 분리 못함
3. AND 게이트 + TargetRotationDelta — 락온 시 적 추적 영향
4. B안 (rising edge AND/NOT) — 갱신 안 됨 부작용
5. bForceBlend=true — BlendStack swap 안 됨
6. Schema curve / OffsetRootBone HalfLife — 다른 무관 변경
7. ControllerYawRate AND 게이트 (2026-04-28) — **결과 정반대**. 락온이 카메라 자동추적해서 strafe 시 Yaw 14~17, 마우스 회전 시 0~15. 카메라 회전 결과는 신호로 부적절.

## 본질 결론 (2026-04-28, 사용자 포기)

**GASP에서도 Circle_Strafe row 미사용** → SB2 고유 버그가 아니라 chooser의 의도된 데드 row일 가능성. 일반화된 trajectory feature(TurnAngle, AngularVelocity, TargetRotationDelta)만으론 락온 strafe vs circle 분리 자체가 trajectory 개념의 한계. 분리하려면 플레이어 Look 입력값(IA_Look ActionValue) 직접 접근 필요한데 SB2는 C++ `USBCharacter`가 처리하고 BlueprintReadOnly getter 없음 → 엔진팀 작업 필요. 비용 대비 효과 낮음.

## 시도하지 않은 미시도 후보 (다음에 재도전 시)
1. **PC_01_BP_Base에 IA_Look 병렬 BP 바인딩** — C++ 바인딩과 양립 가능 시 가장 가벼운 해법
2. **`USBCharacter::GetCachedLookInput()` UFUNCTION 추가 (엔진팀)** — 정석, 시간 소요
3. **PlayerController.GetInputMouseDelta 직접 호출** — 마우스 한정, EnhancedInput 호환 미검증

## BlendStack 노드 구조
- `AnimGraphNode_BlendStack_0`
- AnimationAsset 핀 = **disconnected (push 방식)**
- BlendTime = 0.2, bLoop = true
- Push 메커니즘: SetStateMachineBlendStackAnim → ChooserOutput → ValidAnimFromChooser → BlendStack

## 해결 방향 후보
1. **Conduit 경유 self-loop transition** (사용자 시도 중, 효과 미확인)
2. **OnStateUpdate_GroundMoving 함수 추가 + State Machine UI 등록**
3. **AnimGraph EvaluateChooser2 + BlendStack.AnimationAsset binding** (Monolith 한계)
4. **Sub-State Machine 분해** (GroundMoving 내부)
5. **Character BP에서 Look Input 직접 노출** (외부 변경)

## Why
사용자 의도: 좌우 strafe 시 Circle_Strafe 차단, 회전 시 Circle_Strafe 진입.
이 둘이 trajectory feature(TurnAngle, AngularVelocity, TargetRotationDelta) 만으로 분리 불가능 = 락온 상태에선 두 케이스 trajectory가 비슷.

## How to apply
- 다음 세션 시작 시 baseline 상태(우리 변경 모두 롤백 완료) 가정
- Conduit self-loop이 동작 안 했다면 → OnStateUpdate 함수 + State Machine UI 등록 (가장 정석)
- 또는 Character BP 쪽 Look Input 게이트 시도

## 진단 변수 추가 이력 (2026-04-28)

### 추가됨
- `_DebugPrevControllerYaw` — float, default 0.0, category `_Debug`
  - 용도: ControllerYawRate (deg/s) 계산용 (좌/우 strafe vs circle 회전 분리 시그널 후보)
  - PrevDesiredControllerYaw (dead, Set 0건)와 무관한 신규 변수

### Monolith add_node 한계 재확인 (DrawDebug 그래프 작업 시도)
1. `add_node K2Node_CallFunction`에 function_name/function_class 주입 안 됨 — 모두 generic K2Node fallback (function="None", pins=[])
2. `add_nodes_bulk`도 동일 (`Missing required parameter: node_type` 후 동일 fallback)
3. **`copy_nodes`는 위험** — offset 미적용 + **원본의 then 연결을 새 노드로 이동**시킴 (실측: K2Node_CallFunction_15.then → ExecutionSequence_1.execute 연결이 K2Node_CallFunction_92.then으로 옮겨짐). 즉시 disconnect_pins/remove_node + connect_pins로 복구 가능하지만 위험.

→ **Monolith 자동화로는 PrintString + 변수 참조 + 수식이 섞인 노드 그룹을 안전하게 추가 불가**. 그래프 노드 추가는 BP 에디터에서 수동.

### PIE 진단용 수동 작업 가이드 (DrawDebug 그래프)
사용자가 PC_01_ABP 에디터에서 직접 추가:

1. **DrawDebug 함수 그래프 열기**
2. **위치**: ExecutionSequence_1의 새 then 핀 추가(우클릭 Add Pin) → 또는 IfThenElse_6의 then 직후 사이에 직렬 삽입
3. **노드 체인 구성**:
   ```
   Branch (Cond=IsLockOn)
     true → 
       TryGetPawnOwner → ?Is Valid → Branch
         true →
           GetController → ?Is Valid → Branch
             true →
               GetControlRotation → BreakRotator(Yaw)
                 ↓
               (Yaw - _DebugPrevControllerYaw) → NormalizeAxis → Abs → DeltaYaw
                 ↓
               GetWorldDeltaSeconds → (DT > 0?) Branch
                 true → DeltaYaw / DT = ControllerYawRate
                          ↓
                        Format Text "[CSH] YawRate={Rate} TrjTurn={Trj} Hyst={H} PrevHyst={PH}"
                          (Trj = Abs(TrjTurnAngle), H/PH = bool 변수)
                          ↓
                        PrintString (Duration=0, TextColor=Yellow=(1,1,0,1), bPrintToScreen=true, bPrintToLog=false)
                          ↓
                        Set _DebugPrevControllerYaw = Yaw  (CurYaw)
   ```
4. **컴파일 + 저장**
5. PIE → 락온 진입 → 좌/우 strafe vs 적 주위 circle 회전을 직접 비교하여 YawRate 임계 결정

### 작동 가설
- 좌/우 strafe (캐릭터가 횡으로 이동) → ControllerYawRate ≈ 0 (카메라/컨트롤러 회전 없음)
- 적 주위 circle (락온 회전) → ControllerYawRate 큼 (카메라가 적 추적하며 회전)
- → 이 신호로 두 케이스를 분리할 수 있는지 PIE 실측 후 결정
