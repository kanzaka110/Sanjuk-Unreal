# 10. 실전 예제 모음

## 10.1 이번 편의 목표

지금까지 배운 FocalRig의 모든 기능을 **실전 프로젝트**에 적용하는 예제 4가지를 다룹니다. 각 예제는 독립적이므로 필요한 것만 골라서 참고하세요.

```
예제 목록:
├── 예제 1: TPS 슈터 캐릭터 (풀 세팅)
├── 예제 2: FPS 무기 반동 시스템
├── 예제 3: NPC 대화 시스템
└── 예제 4: 시네마틱 카메라 연출
```

## 10.2 예제 1: TPS 슈터 캐릭터 (풀 세팅)

### 개요

3인칭 슈터 게임의 플레이어 캐릭터에 FocalRig을 완전히 적용합니다.

```
구현 목표:
✅ 크로스헤어 방향으로 상반신 에이밍
✅ 눈이 조준 대상을 추적
✅ 무기별 반동 패턴 적용
✅ 정지/이동 시 발 고정
✅ 조준 상태 전환 (일반 ↔ 에이밍)
```

### Control Rig 구성

```
CR_TPS_Character 그래프:

[Forwards Solve]
       │
       ▼
[Aim Chain] ─── Target: AimTarget
       │         Alpha: AimAlpha
       │         Pelvis Weight: 0.12
       │         Head Weight: 0.20
       ▼
[Leg Adjustment] ─── Alpha: LegAlpha
       │
       ▼
[Eye Aim] ─── Target: EyeTarget
       │       Alpha: EyeAlpha
       │       Stiffness: 20.0
       │       Damping: 2.0
       ▼
[Recoil] ─── Pattern: CurrentRecoilPattern
       │      IsFiring: bIsFiring
       │      Scale: RecoilScale
       ▼
(끝)
```

### Control Rig 변수 목록

```
Variables:
├── AimTarget (Vector) ─── 조준 타겟 위치
├── EyeTarget (Vector) ─── 눈 추적 타겟 위치
├── AimAlpha (Float) ────── Aim Chain 강도
├── EyeAlpha (Float) ────── Eye Aim 강도
├── LegAlpha (Float) ────── Leg Adjustment 강도
├── bIsFiring (Bool) ────── 발사 중 여부
├── CurrentRecoilPattern ── 현재 반동 패턴
└── RecoilScale (Float) ── 반동 크기 배율
```

### Animation Blueprint 구성

```
ABP_TPS_Character AnimGraph:

[Locomotion State Machine]
  ├── Idle
  ├── Walk
  ├── Run
  └── Jump
       │
       ▼
[Layered Blend Per Bone] (선택: 상/하반신 분리)
       │
       ▼
[Control Rig: CR_TPS_Character]
       │
       ▼
[Output Pose]
```

### Character Blueprint 로직

```
BP_TPS_Character Event Graph:

===== 초기화 =====

Event BeginPlay:
  DefaultRecoilPattern = LoadAsset("DA_Recoil_AssaultRifle")
  CurrentWeapon.RecoilPattern = DefaultRecoilPattern

===== 매 프레임 업데이트 =====

Event Tick:
  // 1. 조준 타겟 계산
  CameraForward = GetControlRotation().GetForwardVector()
  TraceStart = CameraLocation
  TraceEnd = TraceStart + CameraForward × 10000
  LineTrace(TraceStart, TraceEnd) → HitResult
  
  If (Hit)
    AimTarget = HitResult.Location
  Else
    AimTarget = TraceEnd
  
  // 2. Alpha 값 보간
  If (bIsAiming)
    TargetAimAlpha = 1.0
    TargetEyeAlpha = 1.0
  Else
    TargetAimAlpha = 0.0
    TargetEyeAlpha = 0.3  // 비조준 시에도 약간의 눈 추적
  
  CurrentAimAlpha = FInterpTo(CurrentAimAlpha, TargetAimAlpha, DT, 8.0)
  CurrentEyeAlpha = FInterpTo(CurrentEyeAlpha, TargetEyeAlpha, DT, 6.0)
  
  // 3. Leg Alpha (속도 기반)
  Speed = GetVelocity().Length()
  If (Speed < 10)
    LegAlpha = 1.0
  Else If (Speed < 300)
    LegAlpha = Lerp(0.8, 0.2, Speed / 300)
  Else
    LegAlpha = 0.0
  
  // 4. Control Rig에 전달
  AnimInstance.SetControlRigVariable("AimTarget", AimTarget)
  AnimInstance.SetControlRigVariable("EyeTarget", AimTarget)
  AnimInstance.SetControlRigVariable("AimAlpha", CurrentAimAlpha)
  AnimInstance.SetControlRigVariable("EyeAlpha", CurrentEyeAlpha)
  AnimInstance.SetControlRigVariable("LegAlpha", LegAlpha)

===== 무기 발사 =====

Event: OnFirePressed
  AnimInstance.SetControlRigVariable("bIsFiring", true)

Event: OnFireReleased
  AnimInstance.SetControlRigVariable("bIsFiring", false)

===== 무기 교체 =====

Event: OnWeaponChanged(NewWeapon)
  AnimInstance.SetControlRigVariable("CurrentRecoilPattern", 
    NewWeapon.RecoilPattern)
  AnimInstance.SetControlRigVariable("RecoilScale", 
    NewWeapon.RecoilScale)
```

## 10.3 예제 2: FPS 무기 반동 시스템

### 개요

1인칭 슈터에서 무기 반동을 FocalRig으로 구현합니다.

```
구현 목표:
✅ 무기별 고유 반동 패턴
✅ 어태치먼트에 따른 반동 감소
✅ 조준경(ADS) 시 반동 변화
✅ 연사 중 크로스헤어 확대
```

### 반동 데이터 에셋 세트

```
Content/Weapons/RecoilPatterns/
├── DA_Recoil_Pistol         (단발, 작은 반동)
├── DA_Recoil_SMG            (빠른 연사, 작은 반동)
├── DA_Recoil_AR_Default     (중간 연사, 중간 반동)
├── DA_Recoil_AR_Compensated (보정 장착, 줄어든 반동)
├── DA_Recoil_Sniper         (단발, 큰 반동)
├── DA_Recoil_Shotgun        (단발, 매우 큰 반동)
└── DA_Recoil_LMG            (느린 연사, 큰 반동)
```

### 무기 데이터 구조

```
Weapon Data Table 또는 Struct:

struct FWeaponData:
  WeaponName: String
  FireRate: Float (RPM)
  RecoilPattern: DataAsset
  BaseRecoilScale: Float
  ADSRecoilMultiplier: Float  // 조준경 사용 시 배율

예시:
  M4A1:
    FireRate: 700
    RecoilPattern: DA_Recoil_AR_Default
    BaseRecoilScale: 1.0
    ADSRecoilMultiplier: 0.7

  AK-47:
    FireRate: 600
    RecoilPattern: DA_Recoil_AR_Default
    BaseRecoilScale: 1.3
    ADSRecoilMultiplier: 0.65
```

### 어태치먼트 시스템과 연동

```
어태치먼트에 따른 RecoilScale 계산:

BaseScale = Weapon.BaseRecoilScale          // 1.0
× ADSMultiplier (조준 시 0.7, 비조준 시 1.0) // 0.7
× GripMultiplier (그립 장착 시 0.8)          // 0.8
× MuzzleMultiplier (머즐 장착 시 0.85)       // 0.85
= FinalScale                                 // 0.476

→ 풀 어태치먼트 시 반동이 절반 이하로!
→ FocalRig Recoil의 AmplitudeScale에 전달
```

## 10.4 예제 3: NPC 대화 시스템

### 개요

NPC가 플레이어를 자연스럽게 쳐다보고, 대화 중 눈을 맞추는 시스템입니다.

```
구현 목표:
✅ NPC가 범위 내 플레이어를 자연스럽게 쳐다봄
✅ 대화 시작 시 몸과 눈이 플레이어를 향함
✅ 대화 중 눈의 자연스러운 움직임 (Saccade)
✅ 대화 종료 시 자연스럽게 시선 해제
```

### Control Rig 구성

```
CR_NPC_Dialogue 그래프:

[Forwards Solve]
       │
       ▼
[Aim Chain] ─── Target: LookAtTarget
       │         Alpha: LookAtAlpha
       │         Pelvis Weight: 0.08  (NPC는 골반 적게)
       │         Head Weight: 0.30    (머리 위주)
       ▼
[Leg Adjustment] ─── Alpha: LegAlpha (보통 1.0 고정)
       │
       ▼
[Eye Aim] ─── Target: EyeTarget
              Alpha: EyeAlpha
              Stiffness: 12.0  (부드럽게)
              Damping: 2.5
              Saccade Amplitude: 0.4°
              Saccade Interval: 2.0초
```

### NPC Blueprint 로직

```
BP_NPC_Dialogue Event Graph:

===== 감지 시스템 =====

Sphere Collision (반경 500cm):

  OnBeginOverlap(Player):
    // 플레이어가 범위 안에 들어옴
    bPlayerInRange = true
    // 서서히 쳐다보기 시작

  OnEndOverlap(Player):
    // 플레이어가 범위를 벗어남
    bPlayerInRange = false
    // 서서히 시선 해제

===== 매 프레임 =====

Event Tick:
  If (bPlayerInRange)
    // 플레이어의 눈 높이 위치 계산
    PlayerEyeLocation = Player.GetActorLocation() + (0, 0, 65)
    
    // 타겟 설정
    AnimInstance.SetVariable("LookAtTarget", PlayerEyeLocation)
    AnimInstance.SetVariable("EyeTarget", PlayerEyeLocation)
    
    // Alpha 보간 (천천히)
    If (bInDialogue)
      TargetAlpha = 1.0    // 대화 중 완전 주시
      TargetEyeAlpha = 1.0
    Else
      TargetAlpha = 0.5    // 범위 안이지만 대화 전 → 가끔 쳐다봄
      TargetEyeAlpha = 0.7
    
    CurrentAlpha = FInterpTo(CurrentAlpha, TargetAlpha, DT, 3.0)
    CurrentEyeAlpha = FInterpTo(CurrentEyeAlpha, TargetEyeAlpha, DT, 4.0)
  Else
    CurrentAlpha = FInterpTo(CurrentAlpha, 0.0, DT, 2.0)
    CurrentEyeAlpha = FInterpTo(CurrentEyeAlpha, 0.0, DT, 3.0)
  
  AnimInstance.SetVariable("LookAtAlpha", CurrentAlpha)
  AnimInstance.SetVariable("EyeAlpha", CurrentEyeAlpha)
```

### 대화 시 Eye Target 변경

```
대화 중 시선 자연스럽게 만들기:

1. 기본: 대화 상대의 왼쪽 눈 → 오른쪽 눈 → 입 → 다시 눈
   (실제 사람이 대화할 때의 시선 패턴)

2. 구현 방법:
   Timer로 3~5초마다 EyeTarget을 변경
   
   EyeTargets 배열:
   ├── PlayerLeftEye  (왼쪽 눈 본 위치)
   ├── PlayerRightEye (오른쪽 눈 본 위치)
   ├── PlayerMouth    (입 본 위치)
   └── PlayerNose     (코 본 위치)
   
   Timer (3~5초 랜덤):
     RandomIndex = Random(0, EyeTargets.Length)
     NewEyeTarget = EyeTargets[RandomIndex]
     // 보간으로 부드럽게 전환
     EyeTarget = VInterpTo(CurrentEyeTarget, NewEyeTarget, DT, 5.0)
```

## 10.5 예제 4: 시네마틱 카메라 연출

### 개요

Sequencer를 사용한 시네마틱에서 FocalRig으로 캐릭터 연기를 제어합니다.

```
구현 목표:
✅ 캐릭터가 특정 대상을 주시하다가 다른 곳을 봄
✅ 눈이 먼저 반응하고, 몸이 따라감 (자연스러운 반응)
✅ 대화 장면에서 두 캐릭터가 서로를 봄
✅ 긴장감 있는 장면 (빠른 시선 전환)
```

### 시나리오: "적 발견" 장면

```
타임라인 (총 5초):

0.0초 ~ 1.0초: 캐릭터 정면 응시 (Idle)
──────────────────────────────────
  AimAlpha: 0.0
  EyeAlpha: 0.3 (약간의 자연스러운 눈 움직임)
  AimTarget: 전방 (500, 0, 150)

1.0초 ~ 1.5초: 오른쪽에서 소리가 남 → 눈이 먼저 반응
──────────────────────────────────────────────
  AimAlpha: 0.0 → 0.0 (아직 몸은 안 움직임)
  EyeAlpha: 0.3 → 1.0 (눈이 빠르게 오른쪽으로)
  EyeTarget: 전방 → 오른쪽 (500, 300, 150)
  
  → 눈만 먼저 오른쪽을 봄!

1.5초 ~ 2.5초: 몸도 따라서 회전
──────────────────────────────
  AimAlpha: 0.0 → 1.0 (몸이 서서히 따라감)
  EyeAlpha: 1.0
  AimTarget: 전방 → 오른쪽 (500, 300, 150)
  
  → 눈이 먼저 가고, 0.5초 후에 몸이 따라감

2.5초 ~ 3.5초: 적 확인, 긴장
──────────────────────────────
  AimAlpha: 1.0
  EyeAlpha: 1.0
  Saccade Amplitude: 0.3 → 1.0 (긴장하여 눈 떨림 증가)
  
  → 적을 발견하여 눈이 미세하게 떨림

3.5초 ~ 5.0초: 무기 들어올리고 조준
──────────────────────────────────
  AimAlpha: 1.0
  EyeAlpha: 1.0
  Recoil: (준비 상태)
  
  → 무기 애니메이션과 FocalRig이 함께 동작
```

### Sequencer 트랙 구성

```
Level Sequence: LS_EnemyDiscovery

트랙:
├── CineCameraActor
│   ├── Transform (카메라 이동)
│   └── Camera Settings (FOV 변화)
│
├── BP_MainCharacter
│   ├── Animation (기본 Idle 시퀀스)
│   ├── Control Rig: CR_TPS_Character
│   │   ├── AimTarget.X ──── 키프레임 ◆
│   │   ├── AimTarget.Y ──── 키프레임 ◆
│   │   ├── AimTarget.Z ──── 키프레임 ◆
│   │   ├── AimAlpha ──────── 키프레임 ◆
│   │   ├── EyeTarget.X ──── 키프레임 ◆
│   │   ├── EyeTarget.Y ──── 키프레임 ◆
│   │   ├── EyeTarget.Z ──── 키프레임 ◆
│   │   └── EyeAlpha ──────── 키프레임 ◆
│   └── Audio (발소리 등)
│
├── BP_Enemy (적 캐릭터)
│   └── Animation
│
└── AudioTrack (배경음, 효과음)
```

### 두 캐릭터 대화 장면

```
시나리오: 캐릭터 A와 B가 마주보고 대화

트랙 구성:

Character_A:
  Control Rig:
    AimTarget = Character_B의 위치 (고정)
    AimAlpha = 0.6 (적당히 상대를 향함)
    EyeTarget = Character_B의 눈 위치 (시간에 따라 변화)
    EyeAlpha = 1.0

Character_B:
  Control Rig:
    AimTarget = Character_A의 위치 (고정)
    AimAlpha = 0.6
    EyeTarget = Character_A의 눈 위치 (시간에 따라 변화)
    EyeAlpha = 1.0

Eye Target 변화 (자연스러운 아이컨택):
  0초: A → B의 왼쪽 눈
  3초: A → B의 오른쪽 눈
  5초: A → 잠시 아래 (생각하는 듯)
  6초: A → B의 왼쪽 눈 (다시 올려봄)
  ...
```

## 10.6 성능 최적화 가이드

### NPC가 많을 때

```
최적화 전략:

1. LOD 기반 비활성화:
   ├── LOD 0 (가까움): 풀 FocalRig (Aim + Eye + Leg)
   ├── LOD 1 (중간):  Aim Chain만
   ├── LOD 2 (멀리):  FocalRig 비활성화 (Alpha = 0)
   └── LOD 3 (매우 멀리): 애니메이션도 간소화

2. 업데이트 빈도 조절:
   ├── 화면 내 + 가까움: 매 프레임 업데이트
   ├── 화면 내 + 멀리: 2프레임마다 업데이트
   └── 화면 밖: 업데이트 안 함

3. 타겟 계산 최적화:
   ├── Line Trace 대신 직접 위치 참조
   ├── 타겟 캐싱 (매 프레임 재계산 X)
   └── 변화가 없으면 업데이트 스킵
```

### FocalRig 자체 퍼포먼스

```
FocalRig 벤치마크 (공식):

캐릭터 1명당 처리 시간: < 100 마이크로초
= FBIK 노드 하나보다 가벼움!

100명의 NPC × 100μs = 10ms
→ 60FPS 기준 프레임의 60%

하지만 위의 최적화를 적용하면:
  화면 내 NPC: 20명 × 100μs = 2ms
  화면 밖 NPC: 0ms
  → 총 2ms = 프레임의 12%

결론: FocalRig 자체는 매우 가볍지만,
      NPC 수가 많으면 LOD 기반 최적화를 적용하세요.
```

## 10.7 문제 해결 종합 가이드

### 자주 묻는 질문 (FAQ)

```
Q1: Aim Offset과 FocalRig을 같이 쓸 수 있나요?
A: 가능하지만 권장하지 않습니다. FocalRig이 Aim Offset의 상위 호환이므로,
   FocalRig만 사용하면 됩니다. 함께 쓰면 이중 적용되어 과도한 회전이 발생합니다.

Q2: MetaHuman에서 동작하나요?
A: 네! Quick Setup이 MetaHuman 스켈레톤을 자동 감지합니다.
   Eye Aim은 MetaHuman의 페이셜 본에도 동작합니다.

Q3: Multiplayer에서 동기화가 되나요?
A: FocalRig은 클라이언트 사이드에서 동작합니다.
   타겟 위치만 리플리케이트하면 모든 클라이언트에서 동일하게 보입니다.
   FocalRig 자체의 동기화는 필요 없습니다.

Q4: 4족 보행 캐릭터에도 쓸 수 있나요?
A: Aim Chain과 Eye Aim은 4족 보행에도 사용 가능합니다.
   Leg Adjustment는 2족 보행 기준이므로 수동 설정이 필요합니다.

Q5: 기존 프로젝트에 도입할 때 기존 Aim Offset을 제거해야 하나요?
A: 제거하는 것이 깔끔하지만, 당장은 Aim Offset의 Alpha를 0으로 낮추고
   FocalRig을 적용한 뒤, 문제없으면 Aim Offset을 삭제하세요.
```

## 10.8 전체 튜토리얼 요약

```
FocalRig 플러그인 튜토리얼 완료!

배운 내용 총정리:

01편: FocalRig 개념 → Aim Offset을 대체하는 프로시저럴 에이밍
02편: 설치 → Fab에서 다운로드, 플러그인 활성화
03편: 핵심 개념 → Aim Chain, Eye Aim, Recoil, Leg Adjustment
04편: Quick Setup → 5분 만에 동작하는 프로토타입
05편: Aim Chain → 체인 본, 가중치, 각도 제한, Alpha
06편: Eye Aim → 스프링 댐핑, Saccade, 각도/거리 제한
07편: Recoil → 2D 패턴 에디터, 프리셋, 데이터 에셋
08편: Leg Adjustment → IK 기반 발 고정, Max Stretch
09편: BP & Sequencer → 런타임 제어, 시네마틱 연출
10편: 실전 예제 → TPS, FPS, NPC, 시네마틱

핵심 요약:
- "노드 하나 놓으면 Quick Setup이 다 해줌"
- "퍼포먼스는 FBIK보다 가벼움"
- "Aim Offset을 만들 필요가 없어짐"
```

## 최종 체크리스트

이 튜토리얼을 통해 다음을 할 수 있어야 합니다:

- [ ] FocalRig을 프로젝트에 설치하고 활성화할 수 있음
- [ ] Quick Setup으로 기본 에이밍을 빠르게 설정할 수 있음
- [ ] Aim Chain의 가중치와 각도 제한을 커스터마이즈할 수 있음
- [ ] Eye Aim으로 자연스러운 눈 추적을 구현할 수 있음
- [ ] Recoil 시스템으로 무기별 반동 패턴을 만들 수 있음
- [ ] Leg Adjustment로 발 미끄러짐을 방지할 수 있음
- [ ] Blueprint에서 FocalRig을 동적으로 제어할 수 있음
- [ ] Sequencer에서 시네마틱 연출에 FocalRig을 활용할 수 있음
- [ ] 실전 프로젝트에 FocalRig을 적용할 수 있음

---
[← 이전: 블루프린트 & Sequencer 연동](09-Blueprint-Sequencer.md) | [목차로 돌아가기 →](README.md)
