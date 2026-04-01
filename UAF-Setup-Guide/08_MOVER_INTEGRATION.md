# 08. Mover 2.0 연동

[<- 이전: Data Interface](./07_DATA_INTERFACE.md) | [목차](./00_INDEX.md) | [다음: 기술 아키텍처 ->](./09_ARCHITECTURE.md)

---

## 8.1 Mover란?

**Mover**는 기존 **Character Movement Component(CMC)**를 대체하는 차세대 이동 프레임워크입니다.

| 항목 | CMC (기존) | Mover (차세대) |
|------|-----------|--------------|
| 상태 | Production | Experimental |
| 아키텍처 | 모놀리식 | 모듈식 (Mode 기반) |
| 네트워킹 | 내장 | Network Prediction Plugin |
| UAF 통합 | X | MoverAnimNext 플러그인 |
| 확장성 | 상속으로 확장 | Mode 추가로 확장 |

---

## 8.2 필수 플러그인

```
[v] Mover                    -- Mover 핵심
[v] Mover UAF (MoverAnimNext) -- Mover와 UAF 연동
```

---

## 8.3 Mover 기반 캐릭터 생성

### 방법 1: BaseAnimatedMannyPawn 상속

1. Content Browser 우클릭 -> **Blueprint Class** 생성
2. **All Classes** 검색에서 `BaseAnimatedMannyPawn` 선택
3. 이름 지정 (예: `BP_MyMoverCharacter`)

이 클래스에는 Mover Component가 이미 포함되어 있습니다.

### 방법 2: 수동 구성

1. 기존 Pawn/Character BP 열기
2. **Add Component** -> `Mover Component` 추가
3. Mover Mode 설정 (Walking, Flying 등)

---

## 8.4 Mover + UAF + Motion Matching 통합

### 전체 데이터 흐름

```
+-------------------+
| Mover Component   |
| (이동 처리)        |
+--------+----------+
         |
         | Velocity, Acceleration, MovementMode
         v
+-------------------+
| UAF System        |
| (PrePhysics)      |
|                   |
| 1. Trajectory 계산 | <-- Mover 데이터로 궤적 생성
| 2. Graph 실행      |
| 3. Pose 쓰기       |
+--------+----------+
         |
         | Trajectory
         v
+-------------------+
| Animation Graph   |
|                   |
| 1. Chooser 평가    | <-- DB 선택
| 2. Motion Matching | <-- Trajectory + DB로 최적 포즈
| 3. Pose 출력       |
+-------------------+
```

### System EventGraph 구성

```
[Initialize]
     |
     v
[Make Reference Pose]

[PrePhysics]
     |
     v
[Calculate Trajectory]          <- Mover Component에서 궤적 생성
     |                             (바인딩으로 자동 참조)
     v
[Evaluate Animation Graph]      <- AG_MyCharacter 실행
     |                             (Trajectory가 Graph로 전달)
     v
[Write Pose to Mesh]            <- 최종 포즈 적용
```

---

## 8.5 MoverAnimNext 플러그인 역할

`MoverAnimNext` 플러그인은 Mover와 UAF의 Tick 동기화를 담당합니다:

```
MoverComponent Tick  ──>  AnimNextComponent Tick
(이동 계산 완료)           (애니메이션 업데이트 시작)
```

- `RigVMTrait_ModuleEventDependency_MoverComponentTickFunctions` 클래스가 Tick 의존성을 관리
- Mover가 이동을 먼저 계산한 후 UAF가 애니메이션을 업데이트하도록 보장

---

## 8.6 UE 5.7의 Mover 이동 모드

| 모드 | 설명 |
|------|------|
| **Simple Spring Walking** | 두 개의 스프링(속도, 회전)으로 이동 시뮬레이션 |
| **Smooth Walking** | CMC와 유사한 부드러운 이동 (미세 조정 가능) |
| **Flying** | 비행 모드 |
| **Swimming** | 수영 모드 |

---

[<- 이전: Data Interface](./07_DATA_INTERFACE.md) | [목차](./00_INDEX.md) | [다음: 기술 아키텍처 ->](./09_ARCHITECTURE.md)
