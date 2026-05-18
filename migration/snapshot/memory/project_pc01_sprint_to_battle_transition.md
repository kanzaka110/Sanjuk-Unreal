---
name: PC_01 Sprint → LockOn Battle 전환 Montage 구현 계획
description: 락온 스프린트 → 일반 락온 이동 시 180° flip 문제 해결용. 기존 전환 애니 4방향 + FullBody Slot 활용. Montage 기반 override.
type: project
originSessionId: c0b37efc-71b6-4348-a2e2-afba5093f18e
---
## 문제
락온 상태에서 스프린트 → 일반 락온 이동 전환 시 RootDir이 순간 반대 방향으로 돌아 튀는 버그 (저빈도).
원인: Aligned(0°) 상태에서 Sprint Cancel → TargetRotation이 180° 점프 → MM이 reverse pose 선택 가능.

## 해결 전략 — Montage Slot Override
MM 시스템 건드리지 않고 Character BP 레벨에서 전환 Montage 강제 재생.

## 확보된 리소스

**전환 애니 (4방향, 이미 존재):**
```
P_Player_Transition_Sprint_to_Battle_Jog_F_Lfoot   (정면)
P_Player_Transition_Sprint_to_Battle_Jog_LL_Lfoot  (좌측 Large)
P_Player_Transition_Sprint_to_Battle_Jog_RL_Lfoot  (우측 Large)
P_Player_Transition_Sprint_to_Battle_Jog_B_Lfoot   (180° 뒤)
경로: /Game/ART/Character/PC/PC_01/Animation/Body/Jog/
```

**MM DB 포함 확인 (PSD_GroundMovingTransit):**
4개 전환 애니 모두 레퍼런스됨. 즉 MM이 선택 가능한 pose이지만 cost/조건 때문에 선택 안 하는 상황.

**Slot (PC_01_ABP AnimGraph):**
- `FullBody` — MM 출력 덮어쓰기 적합 (AnimGraphNode_Slot_2)
- UpperBody / Sequence / Traversal — 다른 용도

**PC_01_BP 기존 함수:**
- `IsSprinting` (from SBCharacter 부모 클래스)
- CMC Velocity 접근 가능

## 구현 Phase

### Phase 1: Montage 에셋 생성 (Content Browser 수동, 위험도 낮음)
각 전환 AnimSequence를 Montage로 변환:
```
AM_SprintToBattle_F   from  P_Player_Transition_Sprint_to_Battle_Jog_F_Lfoot
AM_SprintToBattle_LL  from  ...LL_Lfoot
AM_SprintToBattle_RL  from  ...RL_Lfoot
AM_SprintToBattle_B   from  ...B_Lfoot
```
- Slot: `FullBody`
- Blend In: 0.1 / Blend Out: 0.15

### Phase 2: PC_01_BP 이벤트 로직 (수동, Monolith 사용 금지)
```
IA_Sprint.Released 이벤트:
  IF IsLockOn AND Velocity.Size() > 300:
    angle = NormalizedDeltaRotator(LockOnTarget 방향, Character Forward).Yaw
    montage = 각도별 선택:
      |angle| < 45      → AM_SprintToBattle_F
      45 <= angle < 135  → AM_SprintToBattle_RL
      -135 < angle < -45 → AM_SprintToBattle_LL
      |angle| >= 135    → AM_SprintToBattle_B
    PlayMontage(montage)
```

### Phase 3: 튜닝
- Velocity 임계 (300 cm/s 시작값)
- 각도 경계 (45°, 135° 조정)
- Blend 시간

## 이 방식이 안전한 이유

1. **ABP 그래프 변경 없음** — 오늘 세션의 무한루프 함정 회피
2. **Slot 기반 Override** — MM은 계속 돌아감, Montage만 FullBody 덮어씀
3. **Montage 종료 후 자동 MM 복귀** — 자연스러운 흐름
4. **각도별 애니 선택** — 180° 뒤쪽 케이스도 전용 B 애니가 처리

## 오늘 세션 교훈 (통합)

- Monolith로 ABP 내부 그래프 수정 금지 (무한루프, struct 영속성 문제)
- BP 편집은 **에디터 UI 직접** 사용 (수동)
- 파라미터 튜닝이 아닌 **아키텍처 솔루션**이 이 버그의 정답

## 관련 메모리
- project_pc01_lockon_sprint_rotation_bug.md (버그 상세 분석)
- feedback_monolith_graph_editing_risks.md (BP 편집 위험)
- project_pc01_abp_chain.md (ABP 구조)
