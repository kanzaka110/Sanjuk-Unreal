---
name: PC_01 락온 스프린트 정지 반대 회전 버그 (저빈도)
description: 락온 상태 스프린트 정지 중 낮은 빈도로 반대 방향 회전. LockOnSprintChangeOrientModeTime=0.1 감속 중 Orient Mode flip이 주원인 의심.
type: project
originSessionId: c0b37efc-71b6-4348-a2e2-afba5093f18e
---
## 증상
락온 상태에서 스프린트 중 멈출 때, 낮은 빈도로 캐릭터가 반대 방향으로 도는 현상.

## 정확한 재현 조건 (2026-04-21 확정)

```
LockOn 활성
+ Evade(회피) 직후
+ Sprint Start 상태
+ Character Dir == Root Dir (정렬된 aligned 상태, delta≈0)
+ Sprint 해제 (중단)
  ↓
회전 방향이 튐 (spike)
```

**주요 메커니즘 추정:**
- Evade 종료 → 정렬 상태 (delta=0)
- Sprint Start 초반 Velocity 아직 불안정
- `LockOnSprintChangeOrientModeTime=0.1` 후 TargetRotation이 Velocity 방향 → LockOn 타겟 방향으로 flip
- 불안정 Velocity 기반 target → 다음 프레임 급변 → delta spike

**내 180° 가드 접근 실패 이유:**
- 가드는 "delta 180° 근접 flip" 문제 해결용
- 실제는 "aligned(0°) 상태에서 값 급변" 문제 → 완전히 다른 현상
- 가드가 strafe 정상 동작(Delta 빈번한 170°+ 발생)까지 침범해 부작용

## 핵심 함수 구조 (PC_01_ABP)

**UpdateTargetRotation** (40 nodes):
- TargetRotation 계산: `Rotation From X Vector(Velocity)` → Delta(Rotator) 기반
- 분기 코멘트: "Player Input으로 움직일 때" / "Player Input이 없음" / "Strafe일 때" / "Strafe가 아닐 때"
- 핵심 코멘트: **"BP에 LockOnSprintChangeOrientModeTime값으로 LockOn중 Sprint일 때, Character Rotation 변경 값 조절"**

**관련 변수 (PC_01_ABP)**:
- TargetRotation (Rotator), TargetRotationDelta (double)
- TargetRotationAtBeginState, TargetRotationDeltaAtBeginState
- IsLockOn / PrevIsLockOn, IsStrafe / PrevIsStrafe, bPrevIsMoving, bPrevIsStart, bPrevIsWriggling
- bNonInputVelocity, Velocity, TrjFutureVelocity

## LockOnSprintChangeOrientModeTime

- PC_01_BP에선 변수 리스트에 없음 → **부모 C++ 클래스(SBPCActorBase 유사)에 정의**
- 현재 값: **0.1초** (2026-04-20 확인)
- 의미: 락온+스프린트 → 정지 시 Orient Mode가 "Movement 방향"에서 "LockOn 타겟 방향"으로 전환되는 딜레이

## 원인 가설 (3중 복합)

1. **0.1초는 감속 중 전환** — 스프린트 해제 후 0.1초 시점에 속도 ~400 cm/s 잔존 (CMC 기본 감속률 기준). Velocity 기반 TargetRotation이 아직 "이동 방향"을 명확히 가리킴.

2. **180° 점프** — Orient Mode flip 순간 TargetRotation이 "Velocity 방향(앞)"에서 "락온 타겟 방향(뒤)"로 즉시 점프. 타겟이 정확히 등 뒤에 있으면 180°.

3. **최단 경로 모호성** — Delta(Rotator)의 좌/우 회전 선택이 정확히 180°에서 flip. 기존 회전 관성(질주 중 작은 회전)에 끌려 반대 방향 선택 가능.

## 저빈도 조건 (3중 동시 만족)

- 락온 타겟 각도 ≈ 160~180° (등 뒤)
- Velocity magnitude at orient-flip 순간 ≈ 임계값
- 180° 근접 시 left/right 선택 flip

## 확증 + 해결 테스트

1. `LockOnSprintChangeOrientModeTime = 0.5`로 증가 → 감속 완료 후 전환
   - 버그 사라짐: Time 짧음이 단독 원인 확정
   - 감소하지만 잔존: Time + 점프 보간 둘 다 필요
   - 변화 없음: 다른 원인 (MM/Chooser/Inertialization)

## 해결 방향 옵션

A. Time 단순 증가 (0.5초) — 반응 지연 트레이드오프
B. 속도 임계 기반 전환: Velocity.Size() < 100 이하로 떨어진 뒤 Orient Mode flip — 코드 수정 필요
C. Orient Mode 전환 시 TargetRotation SLerp 보간 0.3초
D. 180° 근접 시 회전 방향 강제: 입력 있던 쪽 or 회전 추세 방향

## 2026-04-21 시도/실패 기록

**옵션 A (0.5초)**: 실패 — 모션이 더 꼬임. 정지 상태에서 180° 점프가 더 잘 보이게 됨. 0.1초 원복.

**옵션 D (Delta 180° 근접 가드)**: 시도 실패 + 부작용 악화. UpdateTargetRotation의 Delta_18 경로에 `abs(delta) > 170 AND abs(prev) > 0.1 → sign(prev) * abs(current)` 로직 삽입. 결과:
- 락온 strafe에서 Delta가 빈번히 170° 넘음 → 가드 매 프레임 발동
- `sign(prev)` 고정이 좌우 strafe 전환을 방해
- **왼쪽 strafe 입력 시 오른쪽 strafe 모션 선택됨** (MM에 잘못된 delta 부호 전달)
- 완전 롤백 필요 → P4 revert 없이 connect_pins 재연결로 복구 가능

**교훈:**
- Delta_18은 락온 strafe에서도 활성 경로 → 함부로 수정하면 strafe 파손
- 진짜 가드 필요 시 **더 엄격한 컨텍스트 게이팅** 필수:
  - `IsLockOn && !IsStrafe && (Velocity.Size() 감속 중) && (Sprint 해제 직후 N초)` 등
- 또는 **Delta_18이 아닌 Delta_55(RootTransform 기반)** 경로만 타겟팅
- 가장 안전: 코드 수정 대신 팀에 공식 이슈로 보고 → 엔지니어가 설계 레벨에서 해결

## 권장: 이 버그는 저빈도 엣지케이스이므로 팀에 이슈 제보하고 수용

## 참고 에셋 경로
- `/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP`
- `/Game/ART/Character/PC/PC_01/Blueprint/PC_01_BP`
- `UpdateTargetRotation` (ABP 함수)
- `GetOffsetRootRotationMode` / `GetOffsetRootTranslationMode` (ABP 함수, 20/16 노드)
