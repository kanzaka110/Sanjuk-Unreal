---
name: Groom 헤어 튐/덜덜의 진짜 원인 우선순위 (UE 5.7 / SB2)
description: PC_01 케이스에서 검증된 jitter / 무브먼트 튐 / 씬전환 튐 / 프레임드랍 튐 원인 우선순위 + 메커니즘.
type: feedback
originSessionId: 6d37eb50-96ec-4182-8e48-1395df67c432
---
# Groom 헤어 튐/덜덜 진단 우선순위

## 룰

PC_01 케이스(2026-04-29) 진단으로 검증된 우선순위. 헤어 튐 진단 시 이 순서로 의심.

## 원인 우선순위 (높을수록 결정적)

### P0 — ProjectStretch=True
- **메커니즘**: XPBD post-projection이 한 frame 내 segment 길이 위배를 강제로 펼침. 캐릭터 빠른 이동/회전/씬 전환 시 본 root만 점프 → strand tip 관성 뒤처짐 → 길이 위배 → 폭발성 stretch correction
- **증상**: 무브먼트 튐, 씬 전환 튐, 프레임 드랍 시 튐 모두 직격
- **처방**: `ProjectStretch=False` (전 그룹). solve만으로 길이 보존 충분

### P1 — GravityPreloading=0
- **메커니즘**: 시뮬 시작/리셋 시 즉시 풀 중력 적용 → 첫 프레임 큰 acceleration → 가시적 "팝"
- **단**: GravityPreloading은 **AngularSprings 솔버 전용** (CosseratRods/Custom에선 무시) — 메모리 reference_groom_physics_params 참조
- **처방 (CosseratRods)**: 시뮬 워밍업은 GroomComponent의 `bResetSimulationOnAttach` + 짧은 invisible 시뮬 first-frame skip으로 처리

### P1 — Underdamped Bend
- **메커니즘**: BendDamping 0.005 + BendStiffness 0.20 → critical damping의 1/40 → 매 시뮬 시작마다 ringing 발생 → "덜덜"
- **처방**: `BendDamping 0.005 → 0.015~0.020` (전 그룹). swing 보존하려면 0.020 이하

### P2 — Head 본 캡슐 부재 + ProjectCollision=True
- **메커니즘**: SkeletalMesh의 PhysicsAsset에 head 본 캡슐 없음 → strand가 머리 메시 통과 → spine_04/neck_02 캡슐로 강하게 push-out → 진동
- **처방**: PhAT에서 head 본에 Sphyl 추가 (메시보다 1~2mm 안쪽). 추가 전까지 ProjectCollision=False

### P2 — SubSteps 부족 (특히 빠른 모션 그룹)
- **메커니즘**: 한 프레임 dt를 N등분. N이 작으면 빠른 모션 시 sub-dt가 커서 위배 폭증
- **PC_01 케이스**: Grp 4 SubSteps=4 (Density 2.0 + CollisionRadius 0.5인데도)
- **처방**: 무거운/빠른 그룹은 SubSteps 8~16

### P3 — 프레임 드랍 시 timestep 의존성
- **메커니즘**: UE Groom은 **adaptive substepping 없음**. dt 2배 → sub-dt 2배 → 위배 4배 (위치 오차 dt²) → ProjectStretch=True와 결합 시 폭발 직격
- **처방 우선순위**: ProjectStretch=False > StretchStiffness 500→200 > SubSteps ↑ > 게임 측 frame cap

## How to apply

헤어 jitter/튐 진단 시:
1. **먼저 ProjectStretch 끄고 테스트** (가장 빠른 효과 검증)
2. BendDamping 0.005 발견 시 즉시 0.015~0.020으로 (jitter 직격)
3. Head PhysicsAsset에 head 본 캡슐 있는지 확인 (없으면 ProjectCollision=False)
4. 프레임 드랍 시 악화되면 timestep 의존성 — ProjectStretch + StretchStiffness 콤보 처방
5. **IterationCount는 용의자 제외** (별도 메모리)

## PC_01 검증 사례 (2026-04-29)

활성본 PC_01_Hair_01에서 발견된 조합:
- 모든 그룹 ProjectStretch=True → 무브먼트 튐 직접 원인
- 모든 그룹 BendDamping=0.005 → underdamped jitter
- ProjectCollision=True + Head 캡슐 부재 → 머리 안 통과 진동
- Grp 4 SubSteps=4 → Density 2.0 대비 분해능 부족
- 프레임 드랍 시 위 모두 amplify

## 참고

- 솔버: SB2 `SBStableRodsSystem` (CosseratRods 파생, GravityPreloading 미적용)
- UE 5.7 소스: `cache/ue57_groom/GroomAssetPhysics.h`
- 컴포넌트 레벨 보강: `LinearVelocityScale` 0.7~0.8, `AngularVelocityScale` 0.7, `TeleportDistance` 적정값 (메모리 reference_groom_physics_params)
