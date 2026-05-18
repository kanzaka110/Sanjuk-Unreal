---
name: UE 5.7 Groom Physics 파라미터 완전 레퍼런스
description: CosseratRods 솔버 기준 모든 파라미터 설명/의미/단위/기본값/증감 효과. 헤어 튜닝 단일 진실원.
type: reference
originSessionId: 2ca0199a-2137-4ab5-b982-e90a25c875fe
---
# UE 5.7 Groom Physics 파라미터 레퍼런스

소스: `cache/ue57_groom/GroomAssetPhysics.h` (UE 5.7 브랜치 실측)

## 솔버 종류

- **CosseratRods** ("Groom Rods"): Cosserat rod 이론 기반. strand를 3D 회전 segment 체인으로 모델링. 비틀림/구부림/늘어남 3축 독립 제어. 안정적, 현실적
- **AngularSprings** ("Groom Springs"): 관절 각 스프링. 구현 단순, 한계 있음. `GravityPreloading` 전용
- **CustomSolver**: 사용자 Niagara System (SB2 SBStableRodsSystem1 = CosseratRods 파생)

## 핵심 함정

1. **GravityPreloading은 AngularSprings 전용.** CosseratRods/Custom에선 무시. UI엔 있지만 읽히지 않음
2. **BendDamping/StretchDamping 기본값은 0.001** — 0.1/1.0 값은 "스프링 죽임". 딱딱한 헤어의 주범
3. **GravityVector.Z 기본 = -981 cm/s²**. -1 같은 값은 버그
4. **StretchStiffness 단위 GPa.** 헤어는 100~1000이 일반적
5. **Stiffness 낮추기보다 Damping 낮추는 게** "흐르는 느낌" 핵심

## 파라미터 그룹별 개념

### Solver Settings (솔버 엔진)
- `bEnableDeformation`: 렌더 strand 매끄럽게 하는 Deformer on/off
- `EnableSimulation`: 그룹 물리 시뮬 on/off
- `NiagaraSolver`: 솔버 모델 (CosseratRods/AngularSprings/Custom)
- `SubSteps`: 프레임 내부 시간 분할 수 (빠른 모션 안정성)
- `IterationCount`: XPBD 반복 수 (제약 엄격도)
- `GravityPreloading`: rest pose 중력 보정 (AngularSprings 전용)
- `bForceVisible`: 가이드 가시화 (디버그)

### External Forces (외력)
- `GravityVector` cm/s² (기본 -981): **복원력의 원천.** 스윙이 돌아오게 만듦
- `AirDrag` 0~1 (기본 0.1): 속도 비례 공기 저항, `F = -AirDrag × v`
- `AirVelocity` cm/s: 바람 속도 벡터

### Bend Constraint (구부림)
- 개념: strand를 "직선으로 돌아가려는 탄성체"로 모델링. rest 각도 대비 편차에 비례한 복원 토크
- `BendStiffness` **GPa** (기본 0.01, 실제 모발 3): 스프링 상수 k
- `BendDamping` 0~1 (기본 0.001): 쇼크업소버 c, 각속도 감쇠
- `BendScale` 커브: 뿌리→팁 stiffness 배율 (긴 헤어 = 팁 0.3)
- `SolveBend`/`ProjectBend`: 제약 적용 스위치

### Stretch Constraint (길이)
- 개념: strand segment 길이를 rest 상태로 유지. 실제 모발처럼 거의 신축 안 함
- `StretchStiffness` **GPa** (기본 1.0, 헤어 100~1000): 인장 강성
- `StretchDamping` 0~1 (기본 0.001): 축방향 파동 감쇠
- `SolveStretch`/`ProjectStretch`: True 필수

### Collision Constraint (충돌)
- 대상: 캐릭터 Physics Asset의 캡슐/스피어/박스
- `CollisionRadius` cm (기본 0.001 = off): strand 주위 감지 반경
- `StaticFriction`/`KineticFriction` 0~1 (기본 0.1): 쿨롱 마찰
- `StrandsViscosity` 0~1: strand 자기 충돌 점성 (뭉침 정도)
- `GridDimension`: 점성 계산 격자 (기본 30³)
- `SolveCollision`/`ProjectCollision`: True 권장
- `RadiusScale` 커브: 길이 따라 반경 배율

### Strands Parameters (가닥 물리)
- `StrandsSize`: 가이드 당 파티클 수 (Size2~32). Size8 표준, Size16 hero
- `StrandsDensity` g/cm³ (기본 1.0, 실제 1.3): 질량 계산. `m = density × π × r² × length`
- `StrandsThickness` cm (실제 0.005~0.01): 질량 제곱 영향
- `StrandsSmoothing` 0~1: 입력 커브 사전 스무딩 (안정성)
- `ThicknessScale` 커브: taper 효과

### Component Simulation Setup
- `bOverrideSettings`: Asset 기본값 대신 Component 값 사용
- `bLocalSimulation` (True 권장): 로컬 좌표 시뮬 (게임용) vs 월드 (시네마틱)
- `LocalBone` (기본 "root" → **"head" 필수 변경**): 시뮬 기준 본
- `LinearVelocityScale` 0~1 (기본 1.0): 선속도 전달 비율
- `AngularVelocityScale` 0~1 (기본 1.0, 권장 0.7): 각속도 전달
- `TeleportDistance` cm (기본 50): 이 이상 이동 시 리셋
- `bResetSimulation`: BP 수동 리셋 트리거

## 파라미터 간 상호작용

- Gravity ↓ + Density ↓: 헤어 부유, 움직임 없음
- Gravity ↑ + BendStiffness ↓: 무거운 머리 축 늘어짐
- BendDamping ↓ + StretchDamping ↓: 생기있지만 영원 진동 위험
- CollisionRadius ↑ + Density ↑: 묵직한 어깨 얹힘
- SubSteps ↓ + Fast Motion: 관통 + 발사 현상

**"이상한 움직임"은 파라미터 2~3개 세트로 판단** (한 값만 보면 안 됨).

## 튜닝 전략 3가지

### "딱딱한 헤어 → 흐르게"
1. GravityVector.Z → -981
2. BendDamping 0.1 → 0.003
3. StretchDamping 1.0 → 0.05
4. StrandsDensity 0.05 → 0.25
5. BendScale 팁 1.0 → 0.3

### "뒤통수 들림 / 특정 모션 튐"
1. GravityVector.Z = -981
2. SolveStretch = True
3. Component LocalBone = "head"
4. AngularVelocityScale 1.0 → 0.7

### "관통 / 어깨 박힘"
1. CollisionRadius ↑ (최소 2.0)
2. ProjectCollision = True
3. SubSteps 5 → 8
4. Physics Asset head/shoulder 캡슐 확인

## PC_01 실사례 (2026-04-23)

`PC_01_Hair_Sanjuk` Group 0 (Hero, Size16):
- Gravity=-1 🔴, BendDamping=0.1 🔴 (100x), StretchDamping=1.0 🔴 (최대)
- SolveStretch=True ✓, CollisionRadius=2.0 ✓
- StrandsDensity=0.05, Thickness=0.01

상세: `project_pc01_hair_gravity_bug.md`
덤프 스크립트: `scripts/dump_pc01_hair_params.py`
