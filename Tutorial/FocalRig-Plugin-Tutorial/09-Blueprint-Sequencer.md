# 9. 블루프린트 & Sequencer 연동

## 9.1 이번 편의 목표

FocalRig을 **블루프린트(BP)**와 **Sequencer**에서 제어하는 방법을 배웁니다. 게임플레이와 시네마틱 양쪽에서 FocalRig을 활용할 수 있게 됩니다.

## 9.2 블루프린트에서 Control Rig 변수 접근

### Animation Blueprint를 통한 접근

```
FocalRig의 노드 설정을 런타임에 변경하려면:

1. Animation Blueprint에서 Control Rig 노드의 변수에 접근
2. Character Blueprint에서 Animation Instance를 가져옴
3. 변수 값을 업데이트

전체 흐름:
[Character BP] → [Anim Instance] → [Control Rig] → [FocalRig 노드]
```

### Step-by-Step: 타겟 위치 전달

```
Character Blueprint (Event Graph):

1. Event Tick 노드

2. 타겟 위치 계산:
   ├── Line Trace (적 탐지)
   ├── Get Actor Location (특정 액터)
   └── Deproject Screen to World (마우스/크로스헤어)

3. Anim Instance 가져오기:
   Get Mesh → Get Anim Instance → Cast to ABP_Character

4. Control Rig 변수 설정:
   Cast 결과 → Set Variable (AimTarget = 계산된 위치)
```

### 구체적인 블루프린트 노드 연결

```
[Event Tick]
     │
     ▼
[Get Player Controller]
     │
     ▼
[Deproject Mouse Position to World]
     │ (World Position, World Direction 출력)
     ▼
[World Position + World Direction × 5000]  ← Line Trace 끝점
     │
     ▼
[Line Trace By Channel]
     │ (Hit Result)
     ▼
[Branch: Did Hit?]
     ├── True: Hit Location 사용
     └── False: Trace End 사용
     │
     ▼
[Get Mesh]
     │
     ▼
[Get Anim Instance]
     │
     ▼
[Set Control Rig Variable: "AimTarget"]
     └── Value: 위에서 계산한 위치
```

## 9.3 주요 변수 제어 목록

### FocalRig에서 BP로 제어할 수 있는 변수들

| 변수 | 타입 | 용도 | 전형적 소스 |
|------|------|------|------------|
| AimTarget | Vector | Aim Chain 타겟 위치 | 적 위치, 크로스헤어 |
| EyeTarget | Vector | Eye Aim 타겟 위치 | 대화 상대 눈 위치 |
| AimAlpha | Float | Aim Chain 강도 | 조준 상태 (0 or 1) |
| EyeAlpha | Float | Eye Aim 강도 | 대화 상태 |
| LegAlpha | Float | Leg Adjustment 강도 | 이동 속도 기반 |
| IsFireing | Bool | 반동 트리거 | 무기 발사 여부 |
| RecoilPattern | Object | 반동 패턴 에셋 | 현재 무기 타입 |

## 9.4 조준 상태 관리 (Aiming State Machine)

### 블루프린트에서 에이밍 상태 관리

```
에이밍 상태 흐름:

[Idle] ←→ [Aiming] ←→ [Firing]
  ↕          ↕           ↕
[Walking] [Aim+Walk] [Fire+Walk]

각 상태별 FocalRig 설정:

Idle:
  AimAlpha = 0.0
  EyeAlpha = 0.5 (주변 관찰)
  LegAlpha = 0.0

Aiming:
  AimAlpha = 1.0
  EyeAlpha = 1.0
  LegAlpha = 1.0

Firing:
  AimAlpha = 1.0
  EyeAlpha = 1.0
  LegAlpha = 1.0
  IsFiring = true

Walking + Aiming:
  AimAlpha = 1.0
  EyeAlpha = 1.0
  LegAlpha = Speed 기반 (0.3~0.8)
```

### Alpha 보간 (부드러운 전환)

```
블루프린트 의사코드:

Variables:
  TargetAimAlpha: Float
  CurrentAimAlpha: Float

Event Tick:
  // 목표 Alpha 결정
  If (IsAiming)
    TargetAimAlpha = 1.0
  Else
    TargetAimAlpha = 0.0
  
  // 부드러운 보간
  CurrentAimAlpha = FInterpTo(
    CurrentAimAlpha,    // 현재 값
    TargetAimAlpha,     // 목표 값
    DeltaTime,          // 프레임 시간
    InterpSpeed: 8.0    // 보간 속도
  )
  
  // Control Rig에 전달
  SetControlRigVariable("AimAlpha", CurrentAimAlpha)

→ IsAiming이 true가 되면, Alpha가 0에서 1로 부드럽게 올라감
→ IsAiming이 false가 되면, Alpha가 1에서 0으로 부드럽게 내려감
```

## 9.5 Sequencer에서 FocalRig 사용

### Sequencer란?

```
Sequencer = UE5의 시네마틱 편집기

- 영화 감독처럼 카메라 앵글, 캐릭터 동작, 조명 등을 타임라인에 배치
- 키프레임 기반으로 값을 시간에 따라 변화
- FocalRig 변수도 Sequencer에서 키프레임 가능!
```

### Sequencer에 Control Rig 트랙 추가

```
1. Level Sequence 에셋 생성 (또는 기존 것 열기)

2. 시퀀서에 캐릭터 액터 추가:
   - Track → Actor To Sequencer → 캐릭터 선택

3. 캐릭터 트랙 확장:
   - Animation → Control Rig 트랙 추가

4. Control Rig 트랙에서 FocalRig 변수 노출:
   - + Channel → AimTarget 추가
   - + Channel → EyeTarget 추가
   - + Channel → AimAlpha 추가
   - 등등...

5. 키프레임 설정:
   - 타임라인에서 원하는 시점으로 이동
   - 변수 값 입력
   - 키프레임 추가 (◆ 아이콘 클릭)
```

### Sequencer 키프레임 예시

```
시네마틱 장면: 캐릭터가 적을 발견하고 조준하는 장면

타임라인:
0초    1초    2초    3초    4초    5초
│──────│──────│──────│──────│──────│

AimAlpha:
0.0────0.0────0.0→1.0──1.0────1.0────
                 ↑
              2초에 에이밍 시작

AimTarget (X):
0──────0──────100→──500──500────500──
                 ↑
              타겟 방향으로 이동

EyeAlpha:
0.5────0.5→1.0──1.0──1.0────1.0────
            ↑
         1.5초에 눈이 먼저 적을 봄 (몸보다 먼저!)
```

> 💡 시네마틱에서는 **눈이 먼저 타겟을 보고**, 몸이 그 다음에 따라가는 것이 자연스럽습니다. Eye Aim Alpha를 Aim Chain Alpha보다 약간 먼저 올리세요.

## 9.6 시네마틱 레이어링

### Sequencer에서 FocalRig + 기존 애니메이션

```
Sequencer 트랙 구조 (위에서 아래로 우선순위):

캐릭터 트랙
├── Animation 트랙: 기본 애니메이션 (Idle, Walk 등)
├── Control Rig 트랙: FocalRig
│     ├── AimTarget: 키프레임으로 시간에 따라 변화
│     ├── AimAlpha: 에이밍 시작/종료 시점
│     └── EyeTarget: 눈이 바라보는 위치
└── Transform 트랙: 캐릭터 위치/회전 (이동 경로)

결과:
- 기본 애니메이션이 재생되면서
- FocalRig이 상반신을 타겟 방향으로 조정
- 눈이 자연스럽게 대상을 추적
- 모든 것이 시네마틱 타임라인에 맞춰 동작!
```

## 9.7 Look At Actor 구현

### 특정 액터를 바라보는 기능

```
블루프린트 구현: "LookAtActor" 기능

Variables:
  LookAtTarget: Actor Reference
  bIsLookingAtTarget: Bool

Function: StartLookAt(TargetActor)
  LookAtTarget = TargetActor
  bIsLookingAtTarget = true

Function: StopLookAt()
  bIsLookingAtTarget = false

Event Tick:
  If (bIsLookingAtTarget AND LookAtTarget is Valid)
    // 타겟 액터의 위치 가져오기
    TargetLocation = LookAtTarget.GetActorLocation()
    
    // 머리 높이 보정 (선택)
    TargetLocation.Z += 60  // 대략 머리 높이
    
    // FocalRig에 전달
    SetControlRigVariable("AimTarget", TargetLocation)
    SetControlRigVariable("EyeTarget", TargetLocation)
    SetControlRigVariable("AimAlpha", 
      FInterpTo(CurrentAlpha, 1.0, DeltaTime, 5.0))
  Else
    SetControlRigVariable("AimAlpha", 
      FInterpTo(CurrentAlpha, 0.0, DeltaTime, 8.0))
```

### 사용 예시

```
// NPC Blueprint에서:

Event BeginOverlap (Trigger Volume)
  → StartLookAt(OtherActor)  // 영역에 들어온 플레이어를 봄

Event EndOverlap (Trigger Volume)
  → StopLookAt()  // 영역을 벗어나면 쳐다보기 중지
```

## 9.8 다중 타겟 우선순위

### 여러 타겟 중 하나를 선택하는 시스템

```
블루프린트 로직:

Function: SelectBestTarget() → Actor

1. 주변의 모든 잠재 타겟 수집
   (SphereOverlap 또는 AI Perception)

2. 각 타겟에 점수 부여:
   ├── 거리 점수: 가까울수록 높음
   ├── 각도 점수: 정면에 가까울수록 높음
   ├── 위협도 점수: 적 > 중립 > 아군
   └── 최근성 점수: 최근 감지된 것이 높음

3. 가장 높은 점수의 타겟 반환

4. FocalRig 타겟으로 설정
   (보간으로 부드럽게 전환)
```

## 9.9 이벤트 기반 제어

### 게임 이벤트에 따른 FocalRig 제어

```
이벤트별 FocalRig 반응:

[무기 발사] → Recoil 트리거
  OnFire() → SetControlRigVariable("IsFiring", true)

[무기 발사 중지] → Recoil 복귀
  OnStopFire() → SetControlRigVariable("IsFiring", false)

[무기 교체] → 반동 패턴 변경
  OnWeaponChanged(NewWeapon)
    → SetControlRigVariable("RecoilPattern", NewWeapon.RecoilData)
    → SetControlRigVariable("FireRate", NewWeapon.FireRate)

[대화 시작] → Eye Aim 활성화
  OnDialogueStart(NPCActor)
    → SetControlRigVariable("EyeTarget", NPC.EyeLocation)
    → SetControlRigVariable("EyeAlpha", 1.0)

[대화 종료] → Eye Aim 비활성화
  OnDialogueEnd()
    → SetControlRigVariable("EyeAlpha", 0.0)

[피격] → 에이밍 흔들림
  OnHit()
    → 일시적으로 AimAlpha를 0.3으로 떨어뜨림
    → 0.5초 후 원래 값으로 복귀
```

## 9.10 퍼포먼스 고려사항

### Blueprint에서의 최적화

```
❌ 피해야 할 패턴:

Event Tick:
  Get All Actors of Class (매 프레임 모든 액터 검색)
  → 매우 비효율적!

✅ 권장 패턴:

BeginPlay:
  타겟 레퍼런스를 캐싱 (한번만 검색)

Event Tick:
  캐싱된 레퍼런스에서 위치만 가져오기
  → 훨씬 빠름!
```

```
추가 최적화 팁:

1. 멀리 있는 캐릭터의 FocalRig 비활성화
   → LOD에 따라 Alpha를 0으로

2. 화면에 안 보이는 캐릭터 스킵
   → WasRecentlyRendered() 체크

3. 타겟 업데이트 빈도 줄이기
   → 30FPS 기반 (매 프레임 대신 격 프레임)
   → 보간으로 부드러움 유지
```

## 체크리스트

다음 단계로 넘어가기 전에 확인하세요:

- [ ] Character BP에서 Control Rig 변수에 접근하는 방법을 이해함
- [ ] 타겟 위치를 Line Trace로 계산하고 전달할 수 있음
- [ ] Alpha를 FInterpTo로 부드럽게 전환할 수 있음
- [ ] Sequencer에서 FocalRig 변수를 키프레임할 수 있음
- [ ] Look At Actor 기능을 구현할 수 있음
- [ ] 게임 이벤트에 따라 FocalRig을 제어할 수 있음

---
[← 이전: Leg Adjustment 시스템](08-Leg-Adjustment.md) | [다음: 실전 예제 모음 →](10-Practical-Examples.md)
