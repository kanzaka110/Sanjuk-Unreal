# [협의 요청] PC_01 월런 — ① 회전 잠금 ② 피격 리액션 연동

작성: 2026-08-03 (애니메이션 TA 협의용 초안)

## 요청 ① 월런 중 캐릭터 회전 잠금 (우선순위 높음)

월런(SB_MOVE_WallRun) 중 스틱 입력 방향으로 캐릭터(캡슐)가 계속 회전합니다. 벽을 따라 달리는 방향으로 회전이 고정되어야 합니다.

### 실측 근거 (2026-08-03 PIE)

- 월런 12회 실측: 캡슐 yaw가 입력 지향(TargetRotation)을 추적하며 최대 260° 회전 (RotationRate 500°/s 패턴)
- 원인: CMC `bOrientRotationToMovement=True`의 PhysicsRotation이 커스텀 모드 중에도 동작
- **BP 레벨 우회 시도 → 불가 확정**: OnMovementModeChanged에서 `bOrientRotationToMovement=false` 세팅 시 **1틱 만에 C++가 True로 재설정** (타임시리즈 실측 — SB2 C++가 이 플래그를 직접 관리). CMC가 오너보다 먼저 틱(bTickBeforeOwner)이라 BP 틱 오버라이드도 무효 → C++ 수정만 가능
- 렛지/래더 등 다른 커스텀 이동은 C++이 회전을 관리해 동일 문제 없음 — 월런 Feature만 회전 억제 미구현으로 보임

### 선례: 래더 Feature의 FacingAxis (동일 처리 요청)

- `SBZoneEnvActorLadderFeatureParams`에는 **`FacingAxis: SplineRight` + `bInvertFacing`** 파라미터가 있고, 래더는 이걸로 캐릭터 회전이 스플라인 기준으로 고정됨 (실동작 확인)
- `SBZoneEnvActorWallRunFeatureParams`에는 `NormalAxis`(벽 노멀용)만 있고 **FacingAxis 계열 파라미터/구현이 없음** (CDO 전수 확인)

### 요청 내용

- **래더 Feature의 FacingAxis 강제 페이싱과 동일한 처리를 `SBZoneEnvActorWallRunFeature`에 추가** — 예: FacingAxis=스플라인 탄젠트(달리는 방향), `WallRunMoveData.Side`에 따라 좌/우벽 invert. 월런 중 입력 기반 회전(PhysicsRotation)은 억제

## 요청 ② 월런 중 피격 리액션 모션 연동

월런 중 피격 시 전용 피격 모션 **P_Player_WallRun_Hit_L / R**이 재생되도록 피격 처리 쪽에 월런 상태 분기를 추가해 주세요. 현재는 월런 전용 피격 모션이 준비되어 있으나 연결 경로가 없습니다.

## 배경

- PC_01 월런 모션 파이프라인은 ABP EventMoving 추저 체인으로 구축 완료 (진입/루프/L·R/점프까지 PIE 검증됨, 2026-08-03)
- 피격 리액션은 ABP 변수 신호 없이 데이터/C++ 주도 몽타주(FullBody 슬롯, `Feedback/Result_Hit_*` 계열)로 재생되는 구조

### PIE 실측 근거 (2026-08-03, 지상 피격 2회 샘플링)

- 피격 순간 ABP `IsFullBodySlotActive=True` (약 0.65s / 강 2.7s) — 피격 = FullBody 슬롯 몽타주 재생 확정
- 피격 중 스테이트 머신은 몽타주 스테이트로 전환 — **ABP 추저 체인에는 재생 에셋 선택권이 없음**
- `RuleMoveFlag`는 피격 내내 None (회피 전용 플래그, 피격 신호 아님)
- 결론: 월런 전용 피격 모션은 **몽타주를 재생하는 쪽(C++/기획 데이터)에서 월런 상태 분기로 클립을 교체해야만 가능** — ABP 단독 구현 불가 (실측 확정)

## 준비된 에셋

| 에셋 | 경로 |
|------|------|
| 우벽 피격 | `/Game/Art/Character/PC/PC_01/Animation/Body/Temp/P_Player_WallRun_Hit_R` |
| 좌벽 피격 | `/Game/Art/Character/PC/PC_01/Animation/Body/Temp/P_Player_WallRun_Hit_L` |

- 스켈레톤: `PC_01_Body_001_Skeleton` (구 Eve 프로토 리타겟, 본트랙 정상 확인)
- 정식 폴더 이동 예정이며 이동 시 경로 재공유

## 필요한 판단 신호 (엔진 측 이미 존재)

- 월런 상태: `SBCharacterMovementComponent`의 `MovementMode == MOVE_Custom && CustomMovementMode == SB_MOVE_WallRun(1)` 또는 `GetWallRunMoveData().bActive`
- 좌/우벽: `GetWallRunMoveData().Side` (`ESBWallRunSide: Right=0, Left=1`) → Side에 따라 Hit_R / Hit_L 선택

## 제안 옵션

1. **C++ 피격 처리 분기**: 피격 리액션 재생 지점에서 월런 상태면 위 두 클립으로 스왑 (Side로 L/R 선택)
2. **데이터 테이블 조건 확장**: 피격 리액션 테이블에 캐릭터 상태(월런) 조건 컬럼이 이미 있거나 추가 가능하다면 데이터 등록 방식 선호

## 확인 요청 사항

- 피격 중/후 월런 유지 정책 (피격 시 월런 강제 이탈인지, 유지 후 복귀인지 — 모션 후처리 방향이 달라짐)
- 재생 방식이 몽타주라면 슬롯(FullBody/UpperBody) 지정 협의
