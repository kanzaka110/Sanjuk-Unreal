# IsPivoting F→B 피벗 완전 해결 — SmoothedVelocity 통일 (2026-05-21)

PC_01_ABP `IsPivoting` 함수의 락온 F→B(앞→뒤) 피벗 실패를 조깅·질주 양쪽에서 해결. 근본원인은 두 분기 공통으로 `bPrevIsMoving`의 속도-dip 의존성이었고, dip-tolerant 신호로 통일해 끝냈다. PIE 로그(SB2.log ANIM_REC)로 단계마다 검증.

## 증상
- 락온 이동 중 F→B 반전 시 피벗 모션이 안 나옴. 다른 방향(L↔R, B→F)은 정상.
- 조깅에서 1차 해결 후, 락온 **질주** F→B는 여전히 전방 루프(`Sprint_Loop_F`)를 유지한 채 미끄러지듯 도는 "매우 이상함".

## IsPivoting 구조 (2분기)
`IsStrafe`로 분기. 두 분기 차이는 피벗 트리거뿐, moving 가드는 공통이어야 함.
```
strafe (IsStrafe=true, 락온 조깅/walk): IsLockOn AND (MoveSide!=PrevMoveSide) AND NOT(TrjIsCircling) AND <moving 가드>
else   (IsStrafe=false, 락온 질주):     (|TargetRotationDelta|>=PivotAngleThreshold[pwm]) AND NOT(TrjIsCircling) AND <moving 가드>
```

## 진단 → 처방 (로그 기반)

### 1. 조깅 F→B (strafe 분기)
- pin D `bPrevIsMoving` → F→B 반전 시 속도 0-통과 dip에 false → ip 죽음. 조깅 피벗은 isf=true 100% 확인 → strafe 분기 처리.
- **처방: pin D `bPrevIsMoving` → `VSizeXY(SmoothedVelocity) > 50`** (dip-tolerant). ✅

### 2. 폐기된 시도 — Branch 조건 `IsStrafe OR IsLockOn`
- 질주(isf=false)를 strafe로 보내려 했으나, 락온 85%(isf=false)가 MoveSide 기반으로 가서 **`Sprint_turn_Stop`에 ip=true 158프레임 헛발동**(회귀). **revert.** (조깅 피벗은 isf=true라 reroute 불필요였음.)

### 3. 질주 F→B (else 분기)
- C항 = 락온이면 XNOR `NOT(bPrevIsMoving)`. 로그 결정적 비교: 우측반전(trd=171, **bpim=true** 얕은 dip) → C=false → ip=false → Chooser가 Sprint_Loop_F 선택. 좌측반전(trd=-165, **bpim=false** 깊은 dip) → ip=true → 턴. **차이는 bpim뿐, trd(171)·isc(false)는 결백.**
- **처방: C항 XNOR 제거 → `VSizeXY(SmoothedVelocity) > 50`** (strafe와 통일). 우측반전도 ip=true → `Sprint_Turn_R_180` 발동. ✅

### 4. 보강 — SmoothedVelocity 벡터-0 함정
- `VSizeXY(SmoothedVelocity)>50` 단독은 질주 반전 중 ip 깜빡임(노이즈). SmoothedVelocity는 **벡터**라 전→후 반전 시 크기가 0 통과(|sv|≈7), raw 속도(sp)와 위상 어긋남.
- **처방: moving 가드 = `( VSizeXY(SmoothedVelocity)>50 ) OR ( Speed2D>50 )`** (else 분기 적용). 두 신호가 서로의 0-통과를 메움 → ip 반전 내내 안정 true. ✅

## 최종 상태
| 항목 | 상태 |
|---|---|
| 조깅 F→B | ✅ strafe 분기 `SmoothedVelocity>50` |
| reroute 정지 오발 회귀 | ✅ revert |
| 질주 F→B 턴 발동 | ✅ else 분기 XNOR→`SmoothedVelocity>50` |
| ip 깜빡임(벡터-0) | ✅ `OR(Speed2D>50)` 보강 |

## 핵심 통찰
- **`bPrevIsMoving`(1프레임 lag)은 피벗 게이트로 부적합** — 반전 dip 깊이에 따라 켜졌다 안 켜졌다. `SmoothedVelocity`가 dip-tolerant 대안.
- **SmoothedVelocity는 벡터라 방향 반전 시 크기 0-통과** → raw `Speed2D`와 OR로 보완.
- 질주 trd는 락온에서도 170°까지 커서 트리거로 충분(초기 "락온 TRD blind" 가설은 질주엔 틀림).
- **Chooser가 IsPivoting을 컬럼으로 읽어** 질주 Turn vs Loop 선택 → ip가 실제 레버(re-transit뿐 아니라 Chooser 경유).

## 잔여 (새 작업 — MM/Chooser, IsPivoting 밖)
- **질주 반전 onset 1~3프레임 `Sprint_turn_Stop_B` 끼임 = 노이즈 잔존.** 로그: trd≈0·**ip=false** 순간(반전 직전) MM이 Stop 클립 매칭(searchcost 0.889 차선책) → trd 튀고 ip=true 돼도 클립 이미 Stop_B → 2~3틱 후 Turn 전환.
- IsPivoting으로 해결 불가(ip는 trd≈0에서 false가 맞음). 근본 = 속도 0-통과 시 트라젝토리가 "정지"로 읽혀 MM이 Stop 매칭.
- 다음 작업 후보: ①re-transit trd≈0 재선택 타이밍 ②Sprint_turn_Stop MM 코스트(고속 억제) ③반전 미래 트라젝토리 예측. Chooser Sprint 행 + 활성 PSD DB부터.

## 참고
- 메모리: `project_pc01_ispivoting_smoothedvelocity.md`
- 관련: `project_pc01_trjiscircling_offdelay.md`, `project_pc01_lockon_directional_start_pivot.md`
- ABP 에셋 변경은 Perforce(SB2) — P4 submit 별도.
