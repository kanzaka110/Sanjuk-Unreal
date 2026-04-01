# 7. Control Rig

## 7.1 Control Rig 개념

Control Rig은 UE5의 프로시저럴 리깅 시스템으로, 스켈레톤을 코드/노드로 제어합니다.
Monolith를 통해 **자연어로 Control Rig 그래프를 조작**할 수 있습니다.

### Monolith에서 할 수 있는 것

- Control Rig 그래프 조회/분석
- 노드 추가 및 와이어링
- 변수 생성 및 관리
- 솔버 구성

## 7.2 Control Rig 분석

### 기존 Control Rig 조회

```
프로젝트의 모든 Control Rig 에셋을 찾아줘
```

```
CR_Mannequin_Body의 그래프 구조를 분석해줘.
어떤 노드와 변수가 있는지 보여줘
```

### 변수 확인

```
CR_Mannequin_Body에 정의된 모든 변수를 보여줘.
타입, 기본값, 카테고리 포함해서
```

## 7.3 Control Rig 수정

### 변수 추가

```
CR_Mannequin_Body에 다음 변수를 추가해줘:
- IK_Foot_L (Transform) - 왼발 IK 타겟
- IK_Foot_R (Transform) - 오른발 IK 타겟
- FootIK_Alpha (Float, 기본값 1.0) - IK 블렌딩
```

### 노드 와이어링

```
CR_Mannequin_Body의 Forward Solve에
Two Bone IK 노드를 추가해줘:

- 본: foot_l → calf_l → thigh_l
- IK 타겟: IK_Foot_L 변수
- 알파: FootIK_Alpha 변수
```

## 7.4 IK Rig & Retargeter

### IK Rig 조회

```
프로젝트의 IK Rig 에셋을 모두 보여줘
```

### IK 체인 매핑

```
IK_Mannequin의 체인 매핑을 보여줘.
어떤 본 체인이 설정되어 있는지 확인
```

### Retargeter 설정

```
IK Retargeter의 소스와 타겟 매핑을 확인해줘.
누락된 체인 매핑이 있으면 알려줘
```

## 7.5 Physics Asset

### Physics Asset 조회

```
SK_Mannequin의 Physics Asset을 분석해줘.
바디 수, 컨스트레인트 설정을 보여줘
```

### 바디 프로퍼티 수정

```
Physics Asset의 "spine_03" 바디를
Kinematic에서 Simulated로 변경해줘.
Collision Preset은 Ragdoll로 설정
```

## 7.6 Skeleton 관리

### 소켓 추가

```
SK_Mannequin 스켈레톤에 소켓을 추가해줘:
- "WeaponSocket" (hand_r 본에 부착)
- "ShieldSocket" (hand_l 본에 부착)
- "HeadSocket" (head 본에 부착, 오프셋 Z +10)
```

### 가상 본 추가

```
SK_Mannequin에 가상 본 "VB_WeaponAim"을 추가해줘.
소스 본: hand_r
타겟 본: head
```

### 커브 관리

```
SK_Mannequin의 애니메이션 커브 목록을 보여줘
```

## 7.7 PoseSearch

### 스키마 생성

```
PoseSearch 스키마를 만들어줘:
이름: PS_Locomotion_Schema
트래킹할 본: pelvis, foot_l, foot_r
히스토리 길이: 0.3초
예측 길이: 0.5초
```

### 데이터베이스 관리

```
PoseSearch 데이터베이스에 다음 시퀀스를 추가해줘:
- Walk_Fwd
- Walk_Bwd
- Walk_Left
- Walk_Right
- Jog_Fwd
```

## 체크리스트

- [ ] Control Rig 에셋 조회 및 분석 성공
- [ ] 변수 추가 성공
- [ ] IK Rig/Retargeter 설정 확인
- [ ] Skeleton 소켓/가상 본 추가 성공

---
[← 이전: Animation Blueprint](06-Animation-Blueprint.md) | [다음: 실전 예제 →](08-Practical-Examples.md)
