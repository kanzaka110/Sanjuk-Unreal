# 8. 실전 예제

## 예제 1: Third Person 캐릭터 완전 로코모션 세팅

### 목표
Third Person 템플릿의 캐릭터에 완전한 로코모션 시스템을 AI로 구축합니다.

### 프롬프트

```
Third Person 캐릭터의 완전한 로코모션 시스템을 만들어줘:

=== Step 1: BlendSpace ===
BS_Locomotion (1D):
- Speed 0: Idle
- Speed 150: Walk
- Speed 300: Jog
- Speed 600: Sprint

=== Step 2: AnimMontage ===
AM_Jump:
- 섹션: JumpStart, JumpLoop, JumpEnd
- 블렌드 인/아웃: 0.15초

=== Step 3: Animation Blueprint (ABP_Character) ===
State Machine "Locomotion":
- Idle: Idle 루프
- Moving: BS_Locomotion (Speed 바인딩)
- Jump: Jump_Start → Jump_Loop → Jump_End 순차 재생

트랜지션:
- Idle ↔ Moving: Speed 기준 (임계값 10)
- Moving → Jump: IsInAir == true
- Jump → Idle: !IsInAir && 착지 완료

AnimGraph:
- Locomotion State Machine → Layered Blend → Output Pose
- UpperBody Slot → Layered Blend (상체 오버라이드)

=== Step 4: 스켈레톤 소켓 ===
- WeaponSocket (hand_r)
- BackpackSocket (spine_03)

모든 에셋은 /Game/Characters/MyCharacter/ 폴더에 생성해줘
```

### 예상 결과
- BS_Locomotion.uasset (BlendSpace)
- AM_Jump.uasset (AnimMontage)
- ABP_Character.uasset (Animation Blueprint)
- SK_Mannequin에 소켓 2개 추가

## 예제 2: 전투 시스템 애니메이션

### 프롬프트

```
전투 캐릭터의 공격 애니메이션 시스템을 만들어줘:

1. AnimMontage 3개:
   - AM_LightAttack: 빠른 공격, 0.8초
     섹션: Windup(0-0.2), Strike(0.2-0.5), Recovery(0.5-0.8)
   - AM_HeavyAttack: 강한 공격, 1.2초
     섹션: Charge(0-0.4), Strike(0.4-0.8), Recovery(0.8-1.2)
   - AM_Dodge: 회피, 0.6초
     블렌드 인: 0.1초, 블렌드 아웃: 0.2초

2. 각 Montage에 Notify 추가:
   - AM_LightAttack: "EnableHitbox" (0.2초), "DisableHitbox" (0.5초)
   - AM_HeavyAttack: "EnableHitbox" (0.4초), "DisableHitbox" (0.8초)
   - AM_Dodge: "InvincibleStart" (0초), "InvincibleEnd" (0.5초)

3. Animation Blueprint에 Combat State 추가:
   - Idle → Combat_Idle (IsInCombat)
   - Combat_Idle: 전투 대기 포즈 루프
   - Combat_Idle에서 Montage 슬롯으로 공격 재생

모든 에셋은 /Game/Combat/Animations/ 폴더에 생성
```

## 예제 3: NPC 순찰 애니메이션

### 프롬프트

```
NPC 순찰 시스템의 애니메이션을 세팅해줘:

1. 2D BlendSpace "BS_NPC_Movement":
   X: Direction (-180 ~ 180)
   Y: Speed (0 ~ 400)

   5x3 그리드:
   - 정면 (0도): Idle, Walk_Fwd, Run_Fwd
   - 좌측 (-90도): Idle, Walk_Left, Run_Left
   - 우측 (90도): Idle, Walk_Right, Run_Right
   - 후면 (180도): Idle, Walk_Bwd, Run_Bwd
   - 대각 (45도): Idle, Walk_FwdR, Run_FwdR

2. Animation Blueprint "ABP_NPC":
   State Machine:
   - Idle: 대기 (랜덤 변형 3개)
   - Patrol: BS_NPC_Movement 사용
   - Alert: 경계 포즈
   - Chase: Run_Fwd

   트랜지션:
   - Idle → Patrol: HasPatrolPath
   - Patrol → Alert: SeePlayer
   - Alert → Chase: ConfirmThreat (2초 후)
   - Chase → Patrol: LostPlayer
   - Any → Idle: Speed < 5

3. Aim Offset "AO_NPC_Head":
   NPC 머리가 플레이어를 바라보도록
   Yaw: -60 ~ 60, Pitch: -30 ~ 30
```

## 예제 4: 리타겟팅 파이프라인

### 프롬프트

```
MetaHuman에서 Mannequin으로 애니메이션 리타겟 파이프라인을 세팅해줘:

1. IK Rig 확인:
   - 소스: IK_MetaHuman (MetaHuman 스켈레톤)
   - 타겟: IK_Mannequin (Manny 스켈레톤)

2. IK Retargeter 설정:
   - Spine 체인 매핑 확인
   - Arm (L/R) 체인 매핑 확인
   - Leg (L/R) 체인 매핑 확인
   - Hand/Finger 체인 매핑 (있으면)

3. 누락된 체인 매핑이 있으면 추가해줘

4. 리타겟 결과를 검증할 수 있도록
   테스트용 애니메이션 리스트도 알려줘
```

## 팁: 효과적인 프롬프트 작성법

### DO ✅

```
✅ 에셋 경로를 정확히 지정
   "Idle 애니메이션" (X) → "/Game/Animations/Idle_Anim" (O)

✅ 구체적인 수치 제공
   "적당한 블렌딩" (X) → "블렌드 인 0.2초, Cubic" (O)

✅ 단계별로 나누어 요청
   한 번에 전부 (X) → Step 1: BlendSpace, Step 2: ABP (O)

✅ 결과 확인 요청
   "만들어줘" (X) → "만들고 구조를 다시 보여줘" (O)
```

### DON'T ❌

```
❌ "알아서 해줘" - 결과가 예측 불가능
❌ 에셋이 없는데 사용 요청 - 먼저 존재 확인
❌ 한 번에 너무 많은 작업 - 10개 이하 단위로 나누기
❌ 저장 안 하고 에디터 닫기 - 작업 후 반드시 저장
```

## 체크리스트

- [ ] 예제 1 또는 2를 따라해봄
- [ ] AI 생성 결과를 UE 에디터에서 확인
- [ ] 필요한 부분을 추가 프롬프트로 수정
- [ ] 완성된 에셋 저장

---
[← 이전: Control Rig](07-Control-Rig.md) | [다음: 트러블슈팅 →](09-Troubleshooting.md)
