# 2026-05-15 — PC_01 ABP Transition 함수화 설계

## 배경

현재 PC_01 ABP에서 Pivot(같은 모드 내 방향 변화)과 Transition(모드 자체 변화)이 코드상 섞여 있고, 특히 Transition 처리가 `UpdateVariables` 안 여러 곳에 chain 형태로 분산됨 (Sprint Start chain, Sprint End chain, AnimStance buffer, Phase 3 게이트). 

**핵심 트리거 케이스**: LockOn 상태에서 락온된 캐릭터 반대방향으로 Sprint → Jog 전환 시 회전이 1틱에 180도 점프. 이걸 부드러운 보간으로 다듬기 위해 이미 `UpdateTargetRotation` 그래프에 `RInterpTo` 노드가 들어가 있음 — 거기에 **Transition 함수의 결과값을 흘려보내서 회전 보간 강도를 동적으로 변조**하는 게 목표.

## 분리 원칙

| 축 | 정의 | 처리 |
|---|------|------|
| **Pivot** | 같은 모드 내 방향 변화 | Motion Matching 자체 처리 + sdpt/sdt/csh 히스테리시스 |
| **Transition** | 모드 자체 변화 (Speed 버킷 / LockOn 토글) | **GetTransitionState() 함수 (신규)** + 그 결과값 분배 |

> **Stance/MovementMode 전환은 이번 함수에 포함하지 않음** — 어제 만든 AnimStanceBuffer가 다룸. 추후 확장 시 같은 패턴 적용.

## 자료형 정의

### ETransitionKind (enum)

```
None             // 트랜지션 없음
SpeedBucket      // Walk↔Jog↔Sprint 변화
LockOnToggle     // IsLockOn 변화
Combined         // 둘 다 동시
```

### ETransitionPhase (enum)

```
None             // 트랜지션 없음
Starting         // Alpha 0.0 ~ 0.2 (시작 직후)
Mid              // Alpha 0.2 ~ 0.8 (한창 진행 중)
Ending           // Alpha 0.8 ~ 1.0 (끝나가는 중)
```

### S_TransitionState (struct)

```
Kind                 : ETransitionKind
Phase                : ETransitionPhase
Elapsed              : double      // 시작 후 경과 시간
Remain               : double      // 남은 시간
Duration             : double      // 전체 시간 (Kind별 다름)
Alpha                : double      // 0(시작) → 1(끝). Ease 적용 가능
bShouldSmoothRot     : bool        // 회전 스무스 활성 여부 (Kind != None && Phase != Ending)
SourceSpeedBucket    : ESBWalkMode // 트랜지션 시작 시점 speed
TargetSpeedBucket    : ESBWalkMode // 목표 speed
SourceLockOn         : bool
TargetLockOn         : bool
```

## GetTransitionState() 함수 의사코드

위치: `UpdateVariables` 그래프 내 (또는 신규 함수 그래프로 분리), Sprint End chain 직후 anchor

```
function GetTransitionState() -> S_TransitionState
{
    // === Step 1. 변화 감지 ===
    bSpeedChanged = (PendingWalkMode != PrevPendingWalkMode)
    bLockOnChanged = (IsLockOn != PrevIsLockOn)
    
    // === Step 2. 신규 트랜지션 진입 시 초기화 ===
    if (TS.Kind == None && (bSpeedChanged || bLockOnChanged)):
        if bSpeedChanged && bLockOnChanged:
            TS.Kind = Combined
            TS.Duration = TransitionDuration_Combined  // 기본 0.4s
        elif bSpeedChanged:
            TS.Kind = SpeedBucket
            TS.Duration = GetSpeedBucketDuration(PrevPendingWalkMode, PendingWalkMode)
        elif bLockOnChanged:
            TS.Kind = LockOnToggle
            TS.Duration = TransitionDuration_LockOn   // 기본 0.2s
        
        TS.SourceSpeedBucket = PrevPendingWalkMode
        TS.TargetSpeedBucket = PendingWalkMode
        TS.SourceLockOn      = PrevIsLockOn
        TS.TargetLockOn      = IsLockOn
        TS.Elapsed = 0
        TS.Remain  = TS.Duration

    // === Step 3. 진행 중 트랜지션 갱신 ===
    elif TS.Kind != None:
        TS.Elapsed += DeltaTime
        TS.Remain   = FMax(0, TS.Duration - TS.Elapsed)
        
        if TS.Remain <= 0:
            // 트랜지션 종료
            TS.Kind = None
            TS.Phase = None
            TS.Alpha = 0
            TS.bShouldSmoothRot = false
            return TS

    // === Step 4. Alpha + Phase 계산 ===
    if TS.Kind != None:
        rawAlpha = TS.Elapsed / TS.Duration   // 0 → 1
        TS.Alpha = SmoothStep(rawAlpha, 0, 1) // Ease in/out
        
        if   rawAlpha < 0.2: TS.Phase = Starting
        elif rawAlpha > 0.8: TS.Phase = Ending
        else:                 TS.Phase = Mid
        
        TS.bShouldSmoothRot = (TS.Phase != Ending)

    return TS
}
```

### Duration 값 (튜닝 영역)

| Kind | Duration (s) | 비고 |
|------|--------------|------|
| SpeedBucket: Sprint↔Jog | 0.30 | 핵심 케이스 |
| SpeedBucket: Jog↔Walk | 0.20 |
| SpeedBucket: Walk↔Idle | 0.15 |
| LockOnToggle | 0.20 |
| Combined | 0.40 | 가장 길게 (두 트랜지션 합성) |

`GetSpeedBucketDuration()` 헬퍼 함수가 source/target 조합 보고 위 값 리턴.

## 통합점 1: `UpdateTargetRotation` — RInterpTo InterpSpeed 변조

기존:
```
Current → ┐
Target  → ├─ RInterpTo → NewRot
DeltaT  → ┤
HighSpd → ┘   (고정값 InterpSpeed)
```

변경:
```
Current → ┐
Target  → ├─ RInterpTo → NewRot
DeltaT  → ┤
          │  InterpSpeed = Lerp(LowSpeed, HighSpeed, TS.Alpha)
          │  ↑ Alpha=0 (트랜지션 시작) → LowSpeed (예: 3)  — 느림·부드러움
          │  ↑ Alpha=1 (트랜지션 끝)   → HighSpeed (예: 15) — 정상
          │  ↑ Kind=None              → HighSpeed (정상)
          └─ SelectFloat(bPickA = bShouldSmoothRot,
                         A = LerpResult,
                         B = HighSpeed)
```

LowSpeed/HighSpeed는 새 ABP 변수로 노출 (instance_editable=true) — PIE에서 튜닝.

> `bIsPlayingTransitionBack` 게이트(B_Lfoot 클립 중 strafe 회전 0 잠금)는 보존. 두 처방 공존 — 게이트는 특정 클립 한정, RInterpTo 변조는 일반.

## 통합점 2: Chooser Table — TS.Kind / TS.Phase 컬럼 추가

`/Game/Art/Character/PC/PC_01/StateMachine/GroundMoving.GroundMoving` 의 inner chooser들에 컬럼 추가:

| 컬럼 추가 | 타입 | 활용 |
|----------|------|------|
| `TransitionKind` | enum: ETransitionKind | "Kind != None" 조건으로 트랜지션 전용 row 분기 |
| `TransitionPhase` | enum: ETransitionPhase | "Phase == Starting" 조건으로 트랜지션 진입 직후 row |

특히 **N_LockOn_Moveing chooser** — LockOn 토글 트랜지션 중에 별도 클립 선택 가능 (어제 논의했던 "LockOn 반대방향 turn 모션 끼어듦" 처방 방향과 일치).

## 기존 코드 마이그레이션 매핑

| 기존 변수/플래그 | 새 매핑 | 처리 |
|----------------|--------|------|
| `bIsSprintStartTransition` | `TS.Kind == SpeedBucket && TS.TargetSpeedBucket == Sprinting && TS.Phase != None` | 기존 변수는 새 컴퓨티드로 대체 (또는 derived getter) |
| `bIsSprintEndTransition` | `TS.Kind == SpeedBucket && TS.SourceSpeedBucket == Sprinting && TS.Phase != None` | 동일 |
| `SprintStartTransitionRemain` | `TS.Remain` (Sprint Start 케이스) | TS.Remain 으로 통합 |
| `SprintEndTransitionRemain` | `TS.Remain` (Sprint End 케이스) | TS.Remain 으로 통합 |
| `bCurrentPendingSprinting` / `bJustEnteredSprint` / `bPrevPendingSprinting` | 함수 내부 로컬 변수 | export 안 함 |
| `bIsPlayingTransitionBack` | 보존 (별도 처방) | 통합 안 함 |

## 단계별 구현 계획 (내일 로컬 PC)

### Phase 0: 사전 dump
- `UpdateTargetRotation` 그래프 dump → 현재 RInterpTo 노드 ID + 주변 wire 파악
- `UpdateVariables` 그래프 dump → Sprint Start/End chain 노드 ID

### Phase 1: 자료형 추가
- `ETransitionKind`, `ETransitionPhase` enum 생성 (UAsset 또는 ABP 내 변수 enum)
- `S_TransitionState` struct 생성
- `TS` (S_TransitionState) ABP 변수 추가

### Phase 2: 함수 그래프
- `GetTransitionState` 함수 그래프 생성 (UpdateVariables 외 별도, 또는 UpdateVariables 안 chain)
- 의사코드대로 노드 빌드 (build 스크립트 작성)

### Phase 3: UpdateTargetRotation 통합
- RInterpTo의 InterpSpeed 입력 변경:
  - `Lerp(LowSpeed, HighSpeed, TS.Alpha)` + `SelectFloat(bShouldSmoothRot)`
- LowSpeed, HighSpeed 변수 추가 (instance_editable, 기본 3/15)

### Phase 4: Chooser Table 컬럼 추가
- N_LockOn_Moveing 우선 — TransitionKind, TransitionPhase 컬럼
- 트랜지션 row 추가 (LockOn 토글 중 매칭될 클립)
- 다른 chooser는 일단 패스, 효과 보고 확장

### Phase 5: 마이그레이션
- Sprint Start/End chain 변수들을 derived getter 또는 함수로 대체
- 기존 references 모두 새 변수로 교체

### Phase 6: 검증 (PIE)
- LockOn 반대방향 Sprint → Jog 시 회전 점프 사라지는지 [ANIM_REC] 로그로 검증
- `trd`, `tta`, `Alpha` 필드를 [ANIM_REC]에 추가 (FormatText 확장 — 71필드로)
- 기존 케이스 회귀 없는지 회전 반응 속도 체감

## 새 [ANIM_REC] 필드

| 필드 | 출처 | 용도 |
|------|------|------|
| `tsk` | TS.Kind | 트랜지션 종류 식별 |
| `tsp` | TS.Phase | 트랜지션 단계 |
| `tsa` | TS.Alpha | 보간 알파 (0~1) |
| `tsr` | TS.Remain | 남은 시간 |
| `ris` | RInterpSpeed (최종 입력값) | 실제 회전 보간 속도 확인 |

→ 66필드 + 5 = 71필드. step1의 FORMAT_STR 확장 + step2 wire 추가 필요.

## 의문점 / TBD

1. **함수 위치**: `UpdateVariables` 안 chain vs 별도 그래프 (`UpdateTransitionState` 같은). 별도 그래프가 깔끔하지만 ABP 함수 graph 추가가 Monolith API로 가능한지 확인 필요
2. **Ease curve**: SmoothStep / EaseInOut / Linear 중 어느 게 회전 점프 가장 자연스럽게 잡는지 PIE 튜닝
3. **Mid Phase 정의**: 0.2~0.8 vs 0.3~0.7 — 시각적 효과 차이 PIE에서
4. **Phase != Ending 시 smooth만**: Ending도 smooth 필요할 수도 (특히 Combined). 케이스 보고

## 환경 제약

- 설계는 GCP에서 완성 가능
- 실제 빌드는 로컬 PC + Monolith
- enum/struct 생성이 Monolith API로 가능한지 첫 단계에서 확인 필요 — 안 되면 수동 생성 + 스크립트는 노드만 빌드

---

## 레퍼런스 검증 (2026-05-15 추가)

이 설계의 방향성이 새 발명이 아니라 **세 레이어에서 모두 검증된 표준 패턴**임을 확인:

### 1. SB2 자체 패턴 — 함수 분리

SB2 PC_01 ABP (`cache/sb2/sb2_abp_structure.md`)에 이미 다음 함수들이 존재:
- `IsMoving`, `IsStarting`, **`IsPivoting`** (bool 판정)
- `CalcWalkMode`, `Get_TrajectoryTurnAngle` (계산)
- `UpdatePendingWalkModeWithBuffer`, `UpdateMovementStateWithBuffer` (Buffer 패턴)

→ `GetTransitionState()` 는 이 함수군의 자연스러운 신규 멤버. 특히 **`IsPivoting`이 이미 함수화되어 있는데 `GetTransitionState`가 없는 게 비대칭**이었던 셈.

### 2. SB2 데이터 차원 — Loop/Transition 이미 분리

PoseSearch DB (`cache/sb2/sb2_motion_matching.md`):
| DB | 시퀀스 수 | 역할 |
|----|---------|------|
| `PSD_GroundMoving` | 57 | Loop = Pivot 영역 |
| `PSD_GroundMovingTransit` | **211** | Transition 영역 (가장 큰 DB) |
| `PSD_GroundIdleTransit` | 77 | Stop / TurnInPlace |

→ 데이터 차원 분리는 이미 정착. 코드 차원 분리만 늦었던 것 — 이번 설계가 그 갭을 메움.

### 3. UE 5.7 표준 — Chooser Table 컬럼 패턴

자체 가이드 `Tutorial/AnimNext-Migration-Guide/07_CHOOSER_AND_MOTION_MATCHING.md`:
```
CT_Locomotion 표준 컬럼:
  MovementMode, HasAcceleration, Gait, IsInAir, Direction
```
→ 우리 추가 컬럼 `TransitionKind`, `TransitionPhase`는 같은 추상화 레벨. UAF 7.8절(Movement Direction 처리)이 같은 결의 작업.

### 4. GASP 5.7 / Mover Plugin — 회전 보간의 결정적 레퍼런스

**UE 5.7 Mover plugin의 `USmoothWalkingMode`** (GASP 5.7에 기본 통합) — 정확히 우리 RInterpTo InterpSpeed 변조와 같은 결:

Epic 공식 설명:
> "Designers can tweak the character's ability to turn without losing speed through a **turn strength** parameter, which controls a damper that directly pulls the current velocity direction towards the desired velocity direction."

| 우리 설계 | GASP 5.7 / Mover |
|----------|------------------|
| `RInterpTo` + `InterpSpeed` 동적 변조 | **Spring damper** + "turn strength" 동적 |
| `TS.Alpha`로 InterpSpeed Lerp | turn strength 파라미터 변조 |
| `GetTransitionState` 결과를 분배 | Movement Mode 자체에 spring 내장 |

→ **같은 문제(돌발 회전), 같은 결(damper 기반 보간), 다른 통합 깊이**. GASP는 패러다임 전환 (CMC → Mover), 우리는 기존 ABP에 점진 통합. **효과는 동일**.

### 핵심 외부 레퍼런스 링크

- [USmoothWalkingMode | UE 5.7 Docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/Mover/USmoothWalkingMode)
- [USimpleWalkingMode | UE 5.7 Docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/Mover/USimpleWalkingMode)
- [Mover Plugin | UE 5.7 Docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/Mover)
- [Game Animation Sample Project | UE 5.7 Docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/game-animation-sample-project-in-unreal-engine)
- [GASP 5.7 Update Blog](https://www.unrealengine.com/tech-blog/explore-the-updates-to-the-game-animation-sample-project-in-ue-5-7) (브라우저로 직접 확인 — WebFetch 403)
- [Motion Matching | UE 5.7 Docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/motion-matching-in-unreal-engine)
- [New Movement Model — Daniel Holden](https://theorangeduck.com/page/new-movement-model) — Smooth Walking Mode 설계 철학 (Motion Matching 표준 저자)

### 향후 추가 검증 옵션

- **로컬 PC에서 GASP ABP dump** — `C:\Users\SHIFTUP\Documents\Unreal Projects\GameAnimationSample` 에서 USmoothWalkingMode 실제 파라미터/노드 구성 확인 (가장 직접적)
- **Daniel Holden 블로그 정독** — Spring damper 수학적 기초

### 결론

> 이 설계는 **새 발명이 아니라 Epic이 UE 5.7에서 표준으로 채택한 방향의 점진적·경량 적용**.
> 위험 부담은 낮고, 효과는 검증됨.
