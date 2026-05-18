---
name: PC_01 애니메이션 리그 디버깅 진행 상황
description: PC_01_ABP + AnimLayer_IK + FootClamp 구조. 슬로프/계단 튜닝 중. 2026-04-15 기준 FootPlacement 안착값 도출, 계단 덜컥은 미해결.
type: project
originSessionId: abee917a-80bb-4cf4-a80c-e01a5e7ce6da
---
## 에셋 구조
```
PC_01_ABP (/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP)
  - Chooser Table (EvieAnimChooser_StateMachine) + Motion Matching + BlendStack
  - 서브 SM: GroundIdle/GroundMoving/Falling
  - 타겟 스켈레톤: PC_01_Body_001_Skeleton

PC_01_AnimLayer_IK — 실질 IK 로직
  노드: FootPlacement, LegIK, SlopeWarping, ControlRig ×2 (FootClamp, LookAt), ...

PC_01_CtrlRig_FootClamp — 단순 발 회전 리미터 (6 RigUnit)
  GASP 원본 4단계 대부분 미구현
```

## 현재 안착한 FootPlacement Pelvis 설정 ⭐
```
ActorMovementCompensationMode = SuddenMotionOnly
LinearStiffness = 300      (기본 350)
LinearDamping = 1.0        (기본)
MaxOffset = 10             (기본 50 — lag를 10cm로 cap)
HeelLiftRatio = 0.5
HorizontalRebalancingWeight = 0.5
PelvisHeightMode = FrontPlantedFeetUphill_FrontFeetDownhill
```
**How to apply**: SB2 FootPlacement 조언의 기준점. 미세 조정만 제안.

## 시도하고 실패/포기한 경로
- **LegIK 끄기** → GASP도 둘 다 씀 (feedback_verify_before_assert.md)
- **Slope Warping** → 사용자 판단으로 제거 (5.7 Experimental)
- **CMC 파라미터 튜닝** (MaxStepHeight, bUseFlatBaseForFloorChecks, PerchRadiusThreshold 등) → 계단 덜컥 해결 안 됨. **캡슐 StepUp 텔레포트는 파라미터로 제거 불가 확정**
- **PC_01_BP Mesh Z 보간 자동 구축** (Monolith HTTP로 변수 3개 + 함수 + Tick 연결 성공) → 에디터 freeze 발생, 수동 롤백. `scripts/build_mesh_z_graph.sh`/`connect_mesh_z.py` 커밋만 남김. 재시도 시 SBCharacter 체인에서 `SetRelativeLocation` Tick 호출이 freeze 유발 가능성 조사 필요

## 근본 원인
"무브먼트 콜리전에서부터 튀고 있음" (사용자 관측) → **CMC→Mesh 전파 구간** 문제. FootPlacement 외부 원인. PC_01_AnimLayer_IK2(FootPlacement OFF 변형)에서도 재현.

## 남은 이슈
1. **계단 덜컥 미해결** — Mesh Z 경로 포기 후 대안 탐색 중. 후보:
   - Invisible Ramp Collision Volume (레벨 단, 가장 확실)
   - FootPlacement WorldSpace + 강성 ↑ (Pelvis lag 감수)
   - C++ 엔진 커스텀 (SB2 엔진팀 경유)
2. **PelvisHeightMode 역전 현상** — 내리막 Pelvis 올라감, 오르막 내려감. 원인 미확정 (애니 baked pose vs SB2 커스텀 vs 설정). Alpha=0 테스트 필요

## 참조
- FootPlacement 내부 로직: `reference_foot_placement_gasp.md` (Zhihu 4단계)
- UE 5.7 기본값/enum: `reference_foot_placement_source_5_7.md`
