# 6. Animation Blueprint

Monolith의 가장 강력한 기능 중 하나 — **Animation Blueprint의 State Machine을 AI로 구축**합니다.

## 6.1 AnimBP 분석하기

### 기존 AnimBP 구조 확인

```
ABP_Manny의 전체 구조를 분석해줘.
어떤 State Machine이 있고, 각 스테이트에 어떤 애니메이션이 연결되어 있는지 보여줘
```

### State Machine 상세 조회

```
ABP_Manny의 "Locomotion" State Machine에 있는
모든 스테이트와 트랜지션 규칙을 보여줘
```

## 6.2 State Machine 구축

### 스테이트 추가

```
ABP_Manny의 Locomotion State Machine에 다음 스테이트를 추가해줘:

1. "Idle" - Idle 애니메이션 재생
2. "Walk" - BS_Locomotion_1D BlendSpace 사용
3. "Jump" - Jump_Start 애니메이션 재생
4. "Fall" - Jump_Loop 애니메이션 재생 (루프)
5. "Land" - Jump_End 애니메이션 재생
```

### 트랜지션 생성

```
다음 트랜지션을 만들어줘:

Idle → Walk: Speed > 10
Walk → Idle: Speed < 10
Walk → Jump: IsJumping == true
Jump → Fall: 애니메이션 재생 완료 시
Fall → Land: IsFalling == false
Land → Idle: 애니메이션 재생 완료 시
```

### 트랜지션 룰 설정

```
"Idle → Walk" 트랜지션의 룰을 설정해줘:
- 조건: Speed 변수가 10보다 클 때
- 블렌드 시간: 0.2초
- 블렌드 모드: Cubic
```

## 6.3 Anim Graph 노드 연결

### 노드 추가 및 와이어링

```
ABP_Manny의 AnimGraph에 다음을 설정해줘:

1. "Locomotion" State Machine 노드를 Output Pose에 연결
2. Locomotion과 Output Pose 사이에 Layered blend per bone 노드 추가
3. 상체 슬롯 "UpperBody"를 Layered blend의 Blend Poses에 연결
```

### 스테이트 애니메이션 설정

```
"Walk" 스테이트의 애니메이션을 BS_Locomotion_1D BlendSpace로 설정해줘.
Speed 파라미터는 AnimInstance의 Speed 변수로 바인딩
```

## 6.4 실전: 완전한 로코모션 ABP 만들기

```
새로운 Animation Blueprint를 만들어줘:
이름: ABP_Character_Locomotion
스켈레톤: SK_Mannequin

State Machine "Locomotion":
├── Idle
│   - 애니메이션: Idle_Anim (루프)
│   - → Walk (Speed > 10)
│   - → Jump (IsJumping)
│
├── Walk
│   - BlendSpace: BS_Locomotion_1D (Speed 파라미터)
│   - → Idle (Speed < 10)
│   - → Jump (IsJumping)
│
├── Jump
│   - 애니메이션: Jump_Start
│   - → Fall (애니메이션 완료)
│
├── Fall
│   - 애니메이션: Jump_Loop (루프)
│   - → Land (!IsFalling)
│
└── Land
    - 애니메이션: Jump_End
    - → Idle (애니메이션 완료)

AnimGraph:
- Locomotion → Layered Blend Per Bone → Output Pose
- UpperBody 슬롯 → Layered Blend (상체 오버라이드)

모든 트랜지션 블렌드: 0.2초 Cubic
```

> 💡 이 하나의 프롬프트로 완전한 로코모션 시스템이 만들어집니다!
> 물론 한 번에 완벽하지 않을 수 있으므로, 결과를 확인하고 수정 요청을 하세요.

## 6.5 ABP 디버깅

```
ABP_Character_Locomotion의 구조를 다시 분석해줘.
스테이트, 트랜지션, 노드 연결이 정상인지 확인해줘
```

```
"Walk → Jump" 트랜지션의 조건을 확인해줘.
IsJumping 변수가 올바르게 참조되고 있는지 체크
```

## 체크리스트

- [ ] 기존 AnimBP 구조 분석 성공
- [ ] State Machine에 스테이트 추가 성공
- [ ] 트랜지션 및 룰 설정 성공
- [ ] AnimGraph 노드 와이어링 성공
- [ ] UE 에디터에서 AnimBP 열어서 확인

---
[← 이전: 애니메이션 워크플로우](05-Animation-Workflow.md) | [다음: Control Rig →](07-Control-Rig.md)
