# 4. Quick Setup — 5분 만에 시작하기

## 4.1 이번 편의 목표

이번 편에서는 FocalRig의 **Quick Setup** 기능을 사용하여, 최소한의 설정으로 캐릭터가 타겟을 바라보는 동작을 구현합니다.

```
완성 후 결과:
- 캐릭터의 상반신이 타겟 방향으로 자연스럽게 회전
- 눈이 타겟을 추적
- 발이 바닥에 고정된 채로 유지
- 이 모든 것이 5분 안에 완성!
```

## 4.2 사전 준비

시작 전에 다음이 준비되어 있어야 합니다:

```
✅ FocalRig 플러그인이 설치 및 활성화됨 (02편 참고)
✅ Control Rig 플러그인이 활성화됨
✅ Third Person 템플릿 프로젝트 (또는 Skeletal Mesh가 있는 프로젝트)
✅ 캐릭터에 적용된 Skeletal Mesh와 Animation Blueprint
```

## 4.3 Step 1: Control Rig 에셋 생성

### 새 Control Rig 만들기

```
1. Content Browser에서 원하는 폴더로 이동
   (예: Content/Animation/ControlRig/)

2. 폴더 내에서 우클릭

3. Animation → Control Rig 선택

4. "ControlRigBlueprint" 선택

5. 사용할 Skeletal Mesh 선택
   - Third Person 템플릿: SK_Mannequin 또는 SKM_Manny
   - MetaHuman: 해당 MetaHuman의 스켈레톤
   
6. 이름 지정: CR_FocalRig_Character
   (CR = Control Rig의 약자, 팀 내 네이밍 컨벤션에 맞게 조정)

7. 더블클릭하여 Control Rig 에디터 열기
```

> 💡 Control Rig 에셋 이름에 `CR_` 접두사를 붙이면, 나중에 에셋을 찾기 쉽습니다.

## 4.4 Step 2: Aim Chain 노드 추가

### 노드 배치

```
1. Control Rig 에디터의 Rig Graph에서 빈 공간 우클릭

2. 검색창에 "Aim Chain" 입력

3. "FocalRig Aim Chain" 노드를 클릭하여 추가

4. 노드가 그래프에 배치됨
```

### Quick Setup 적용

```
1. 방금 추가한 Aim Chain 노드를 선택 (클릭)

2. 오른쪽 Details 패널 확인

3. "Quick Setup" 섹션 찾기

4. 드롭다운을 열면 스켈레톤 기반으로 자동 생성된 설정 목록이 표시됨
   예시:
   ├── Setup 1: Spine → Head (권장)
   ├── Setup 2: Spine → Neck
   └── Setup 3: Custom...

5. 첫 번째 설정(Setup 1)이 이미 자동 적용되어 있음
   → 대부분의 경우 이대로 사용하면 OK!

6. 자동으로 채워진 항목 확인:
   - Chain Bones: [spine_01, spine_02, spine_03, neck_01, head]
   - POV Bone: head
   - Aim Axis: 스켈레톤에 맞게 자동 설정
   - Angle Limits: 각 본별 회전 제한
```

> ⚠️ Quick Setup이 자동으로 설정을 채워주지만, 스켈레톤 구조가 표준적이지 않으면 일부 수동 조정이 필요할 수 있습니다.

## 4.5 Step 3: 타겟 설정

### 타겟 핀 연결

```
1. Aim Chain 노드에서 "Target" 입력 핀 찾기

2. 타겟 설정 방법:
   
   방법 A: 변수 사용 (권장)
   ─────────────────────
   a. Rig Graph 왼쪽 "Variables" 패널에서 + 클릭
   b. 이름: AimTarget
   c. 타입: Vector (FVector)
   d. 이 변수를 그래프에 드래그
   e. AimTarget 변수 → Aim Chain의 Target 핀에 연결
   
   방법 B: 직접 값 입력 (테스트용)
   ────────────────────────────
   a. Target 핀의 값을 직접 입력
   b. 예: (X=500, Y=200, Z=150)
   c. 캐릭터 전방 기준 위치
```

### 실행 순서 연결

```
1. "Forwards Solve" 노드의 실행 핀 찾기
   (Control Rig이 자동으로 생성하는 시작 노드)

2. Forwards Solve → Aim Chain 실행 핀 연결
   (흰색 화살표 핀끼리 연결)

3. 이렇게 하면 매 프레임마다 Aim Chain이 실행됨
```

```
완성된 그래프 구조:

[Forwards Solve] ──→ [Aim Chain]
                         ↑
                    [AimTarget 변수]
```

## 4.6 Step 4: Animation Blueprint에 연결

### Control Rig 노드 추가

```
1. 캐릭터의 Animation Blueprint를 열기
   (예: ABP_Manny 또는 ABP_Character)

2. AnimGraph에서 "Control Rig" 노드 검색하여 추가

3. Control Rig 노드의 설정:
   - Control Rig Class: CR_FocalRig_Character (위에서 만든 것)
   - Alpha: 1.0 (완전 적용)

4. 연결 순서:
   [기존 애니메이션 출력] → [Control Rig] → [Output Pose]
```

### 기존 노드와 연결

```
일반적인 AnimGraph 연결:

변경 전:
[State Machine] ──→ [Output Pose]

변경 후:
[State Machine] ──→ [Control Rig] ──→ [Output Pose]
                     (CR_FocalRig_Character)

→ 기존 애니메이션 위에 FocalRig이 덮어쓰는 구조!
→ 기존 걷기/뛰기 등의 애니메이션은 그대로 유지됨
```

## 4.7 Step 5: 블루프린트에서 타겟 전달

### Character Blueprint에서 타겟 업데이트

```
1. 캐릭터 블루프린트를 열기 (예: BP_ThirdPersonCharacter)

2. Event Graph에서 다음 로직 추가:

   Event Tick
       │
       ▼
   [Line Trace / 적 위치 계산 / 커서 위치 등]
       │
       ▼
   [Get Mesh → Get Anim Instance]
       │
       ▼
   [Control Rig의 AimTarget 변수에 값 설정]
```

### 간단한 테스트용 구현 (마우스 커서 따라가기)

```
Event Tick에서:

1. "Get Player Controller" → "Deproject Mouse Position to World"
   (마우스 커서 위치를 월드 좌표로 변환)
   
2. 결과 값(World Position)을 AimTarget 변수에 전달

3. 이렇게 하면 캐릭터가 마우스 커서 방향을 바라봄!
```

> 💡 테스트 단계에서는 마우스 커서를 따라가는 것이 가장 직관적입니다. 나중에 적 AI, 조준점, UI 크로스헤어 등으로 교체하면 됩니다.

## 4.8 Step 6: 결과 확인

### 플레이 테스트

```
1. 에디터 상단의 ▶ Play 버튼 클릭

2. 확인 사항:
   ✅ 캐릭터의 상반신이 마우스/타겟 방향으로 회전하는가?
   ✅ 회전이 자연스러운가? (척추가 부드럽게 커브)
   ✅ 하반신은 영향을 덜 받는가?
   ✅ 걷기/뛰기 애니메이션이 정상적으로 재생되는가?

3. 문제가 있다면:
   - Aim Chain의 Alpha 값 조정 (0.0 ~ 1.0)
   - 각 본의 Weight(가중치) 조정
   - Quick Setup의 다른 옵션 시도
```

## 4.9 Quick Setup 커스터마이즈

기본 Quick Setup이 적용된 후, 필요에 따라 세부 조정할 수 있습니다.

### 자주 조정하는 항목

| 항목 | 설명 | 기본값 | 조정 방향 |
|------|------|--------|----------|
| Alpha | 전체 효과 강도 | 1.0 | 0.0(미적용) ~ 1.0(완전 적용) |
| Weight Per Bone | 본별 회전 비율 | 자동 | 특정 본의 회전을 강조/약화 |
| Angle Limit | 최대 회전 각도 | 자동 | 과도한 회전 제한 |
| Aim Axis | 조준 방향 축 | 자동 | 스켈레톤 방향이 다를 때 |
| Up Axis | 상향 축 | 자동 | 스켈레톤 방향이 다를 때 |

### 미세 조정 팁

```
1. 너무 과하게 돌아가면:
   → Alpha를 0.7 정도로 낮추기
   → 또는 골반(Pelvis) 가중치를 0으로

2. 상반신만 돌리고 싶으면:
   → 골반(Pelvis) 가중치 = 0
   → 하부 척추(Spine_01) 가중치 = 낮게

3. 머리 위주로 돌리고 싶으면:
   → Head, Neck 가중치를 높이고
   → Spine 가중치를 낮추기

4. 부드럽게 전환하고 싶으면:
   → Alpha를 Timeline이나 Interp으로 서서히 변경
```

## 4.10 5분 Quick Setup 요약

```
전체 과정 요약:

[1] Control Rig 에셋 생성 (30초)
         ↓
[2] Aim Chain 노드 추가 + Quick Setup (1분)
         ↓
[3] Target 변수 생성 및 연결 (1분)
         ↓
[4] Animation Blueprint에 Control Rig 노드 추가 (1분)
         ↓
[5] Character BP에서 타겟 전달 로직 추가 (1분)
         ↓
[6] 플레이 테스트 및 확인 (30초)
         ↓
     🎉 완성!
```

## 체크리스트

다음 단계로 넘어가기 전에 확인하세요:

- [ ] Control Rig 에셋을 생성함
- [ ] Aim Chain 노드를 추가하고 Quick Setup을 적용함
- [ ] 타겟 변수를 만들고 연결함
- [ ] Animation Blueprint에 Control Rig 노드를 추가함
- [ ] Character Blueprint에서 타겟 값을 전달함
- [ ] 플레이 테스트에서 캐릭터가 타겟을 바라보는지 확인함

---
[← 이전: 핵심 개념 이해하기](03-Core-Concepts.md) | [다음: Aim Chain 완전 정복 →](05-Aim-Chain.md)
