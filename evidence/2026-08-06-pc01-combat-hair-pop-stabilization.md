# PC_01 점프·회피·공격 헤어 튐 안정화

## 증상

- PC_01 Groom이 고공 낙하, 회피, 공격 모션에서 순간적으로 뒤집히거나 튐.
- 일부 조건에서는 뒤집힌 상태가 시뮬레이션 정지 후에도 복원되지 않음.
- 과도한 Bend 보호는 튐을 줄이지만 헤어 움직임을 얼리는 부작용이 있었음.

## 관찰

- 대상 BP: `/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP`
- 대상 Groom: `/Game/Art/Character/PC/PC_01/Equipment/Hair/PC_01_Hair_01/PC_01_Hair_01_InGame`
- 실제 Groom은 `SBStableRodsSystem / CustomSolver` 사용.
- 인게임 자동 텔레포트 감지는 비활성이라 회피·공격의 일반 회전이 자동 Reset을 발생시키는 경로는 배제됨.
- Actor `GetVelocity` 기반 Spike Guard는 회피의 캡슐 속도 급변은 잡지만, 공격 몽타주의 본 자세 불연속은 직접 감지하지 못함.
- 공격/회피 공통 상태로 `PC_01_ABP.IsEvading OR FullBodySlotWeight > 0.01`을 사용 가능. 단 FullBody 슬롯은 공격 외 FullBody 몽타주도 포함함.
- Groom 그룹 Stretch 실측:
  - G0 `SolveStretch=False / ProjectStretch=False`
  - G1 `False / False`
  - G2 `True / True`
  - G3 `False / False`
  - G4 시뮬레이션 OFF
- G2 `ProjectStretch`를 끄면 뒤집힌 상태가 고착됐고, G2만 다시 켠 뒤 PIE를 재시작하자 고착 현상이 사라짐.

## 후보와 반증

### 1. LinearVelocityScale만 낮추면 해결된다

- `0.00~0.03`에서도 시뮬레이션과 뒤집힘이 지속됨.
- 이 값은 시뮬레이션 ON/OFF가 아니라 캐릭터 선형 관성 전달량임.
- 중력, 바람, 본 이동, CustomSolver 입력은 계속 작동하므로 단독 근본 원인에서 제외.

### 2. BendDampingScale 부족이다

- 컴포넌트 배율을 높여도 뒤집힘이 유지됨.
- InGame Groom 원본 BendDamping도 G0~G3 `0.15~0.20`으로 이미 높음.
- 추가 감쇠 증가는 움직임만 죽이고 해결되지 않아 우선순위에서 제외.

### 3. GroomOptimization이 매 틱 Reset한다

- 함수는 매 틱 호출되지만 시네마틱 상태가 바뀔 때만 에셋·바인딩·SimulationSettings 교체와 Reset을 실행함.
- 일반 게임플레이의 지속적인 회피·공격 튐의 직접 원인에서 제외.

### 4. 점프·착지 HairCap이 원인이다

- `HairCapEnabled=False` A/B에서 증상이 동일함.
- 기존 호출은 제거됐고, 이후 Public 함수와 전용 변수 9개도 사용자 명시 승인 후 백업·컴파일 검증을 거쳐 제거함.

## 적용 결과

### 점프

- `ApplyGroomAirborneHold`
- `IsFalling` 중 Manual Bend 적용, 지상에서 보간 복귀.

### 회피

- 범용 가속도 Spike Guard:
  - `|CurrentVelocity - PrevVelocity| / DeltaSeconds > 8000`
  - Hold `0.15s`
  - Linear/Angular 관성 `×0.1`
  - Spike Bend Boost 현재값 `10`

### 공격

- Combat Ramp:
  - Gate: `IsEvading OR FullBodySlotWeight > 0.01`
  - Start Factor `0.05`
  - Duration `0.10s`
  - 시작 프레임만 관성 전달을 줄이고 0.1초 후 100% 복귀해 공격 중 휘날림 보존.

### 그래프 정리

- 고아 노드 6개 제거.
- 미사용 `ApplyHairCap` 함수와 전용 변수 9개 제거.
- `GroomOptimization`, `ApplyGroomWindCap`, `ApplyGroomAirborneHold`, `ApplyGroomVelCap` 유지.
- 최신 `ApplyGroomVelCap` 감사 결과 106노드 전체가 exec/data dependency closure에 포함되어 추가 안전 삭제 후보는 없음.
- 컴파일 오류 0, 경고 0, 노드 오류 0.

## 결론

- ✅실측: 점프·회피·공격은 하나의 전역 강성값으로 해결하지 않고 상태별로 분리해야 함.
- ✅실측: 회피는 Actor 가속도 Spike Guard, 공격은 0.1초 Combat Ramp가 유효함.
- ✅실측: G2 `ProjectStretch=True`는 뒤집힌 상태의 복원에 필요하며, 전 그룹 ProjectStretch OFF는 금지.
- ✅실측: 과도한 Bend/감쇠는 튐 대신 헤어 프리즈를 만들 수 있으므로 관성 Ramp와 짧은 Hold를 우선함.
- ⚠가설: 공격 중간의 특정 본 포즈 불연속이 남은 순간 뒤집힘의 추가 원인일 수 있음. 공격별 전용 상태 신호 또는 본 기반 입력 계측이 필요함.

## 현재 기준값

| 변수 | 값 |
|---|---:|
| CombatRampDuration | 0.10 |
| CombatRampStartFactor | 0.05 |
| SpikeAccelThreshold | 8000 |
| SpikeHoldTime | 0.15 |
| SpikeVelFactor | 0.10 |
| SpikeBendBoost | 10 |

## 검증

- Monolith v0.20.3 targeted graph/CDO dump.
- 각 Tier 2 변경 전 binary 백업 생성.
- 각 노드·함수·변수 제거 후 Blueprint compile `0 errors / 0 warnings` 확인.
- 최종 fresh readback에서 점프·회피·공격 경로와 사용자 튜닝값 보존 확인.
