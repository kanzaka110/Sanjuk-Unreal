---
name: PC_01_Hair_01 물리 파라미터 확정값 (2026-05-04 라이브)
description: PC_01_Hair_01 Groom 에셋 5그룹 물리 파라미터 최신 라이브 값. Monolith API 직접 조회. 베이스라인 기준점.
type: project
originSessionId: 0b6df417-65f0-4e69-a909-ad2b0a8de52a
---
2026-05-04 14:53 Monolith HTTP API 라이브 조회값. 파일/캐시 아닌 직접 API 조회.

**Why:** 헤어 덜덜림/바람 과반응 튜닝 세션 중 현재 상태 스냅샷.
**How to apply:** 이후 튜닝 시 베이스라인으로 참조. 변경 전 비교 기준점.

## 에셋 정보
- 경로: `/Game/Art/Character/PC/PC_01/Equipment/Hair/PC_01_Hair_01/PC_01_Hair_01`
- 솔버: `CustomSolver` (`/Game/Art/TA/Groom/SBStableRodsSystem`) — SB2 커스텀 CosseratRods
- 라이브 덤프: `C:/Dev/Sanjuk-Unreal/dumps/hair01_cdo.json`

## 그룹별 물리 파라미터 (2026-05-04 라이브)

| Grp | EnableSim | SubSteps | Iter | BendStiff | BendDamp | StretchStiff | StretchDamp | AirDrag | Gravity Z | ProjectCollision |
|-----|-----------|----------|------|-----------|----------|--------------|-------------|---------|-----------|-----------------|
| 0   | True      | 32       | 100  | 0.031     | 0.0028   | 500          | 0.005       | 0.015   | -981      | True            |
| 1   | True      | 32       | 50   | 0.040     | 0.0035   | 1000         | 0.005       | 0.023   | -981      | True            |
| 2   | True      | 5        | 5    | 0.080     | 0.010    | 1000         | 0.010       | 0.030   | -981      | True            |
| 3   | True      | 6        | 5    | 0.050     | 0.007    | 1000         | 0.010       | 0.050   | -981      | True            |
| 4   | True      | 8        | 10   | 0.130     | 0.018    | 1000         | 0.010       | 0.030   | **False** | **False**       |

- Grp 2: SolveStretch=False (Bend만 시뮬, 길이 강체 처리)
- Grp 4: 뒷머리 그룹. ProjectCollision=False (뒷머리 덜덜림 개선 목적)
- 전 그룹 Gravity=-981 정상 (Sanjuk 버전 Grp4=-1 버그는 여기 없음)

## GroomComponent (BP_Sanjuk CDO, 2026-04-30 실측)
- bLocalSimulation = True (False로 끄면 머리 너무 튀어서 유지 필수)
- LinearVelocityScale = 1.0 (최댓값, 올릴 수 없음)
- AngularVelocityScale = 1.0
- LocalBone = "root" (head로 바꾸면 튀어서 유지 필수)
- TeleportDistance = 50
- TeleportDetectionThreshold = 25 (SB2 커스텀 필드 — Hair만)
- bFirstTeleportDetection = True (Hair만)
- WindScale = 0.4 (SB2 커스텀 — 바람 반응 배율)
- PhysicsAsset = Evie_Body_PhysicsAsset (Hair) / None (Fuzz)

## 잔존 이슈 (2026-05-04 기준)
- 뒷머리(Grp 4) 덜덜림 — ProjectCollision=False 적용 후에도 잔존. BendDamp 보강 + AirDrag 낮추기 대기 중
- 바람 과반응 — AirDrag 전 그룹 낮추기 대기 중 (특히 Grp 3=0.050 → 0.020)
- 텔레포트 시 헤어 튀는 것 — bLocalSimulation=True 조건에서 TeleportDistance 자동 reset 비작동. ResetSimulation() 명시 호출 필요
- WindScale=0.4 → 0.2 조정 검토 중

## 튜닝 제약 (확정)
- bLocalSimulation=false 금지: 머리 너무 튀어나옴
- LocalBone 변경 금지: "root"→"pelvis"/"head" 전환 시 튀어나옴
- LinearVelocityScale: 0~1 클램프. 1.0이 최대
- AngularVelocityScale: 0~1 클램프. 1.0이 최대
