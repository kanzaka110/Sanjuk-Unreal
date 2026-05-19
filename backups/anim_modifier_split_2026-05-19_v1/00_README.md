# AnimationModifier 분리 작업 백업 (2026-05-19)

## 목적

`AM_SBFootStepNotifies` (FX/Sound 노티파이 추가) → 두 모디파이어로 분리:
- **AM_SBFootStepNotifies** (기존): 그대로 유지 — FX/Sound 노티파이만 추가
- **AM_SBFootSyncNotifies** (분리 대상): Sync Marker 추가로 변경

## 변경 대상

- 자산 경로: `/Game/Art/TA/AnimModifiers/AM_SBFootSyncNotifies`
- 디스크 경로: `E:/Perforce/SB2/Workspace/Internal/SB2/Content/Art/TA/AnimModifiers/AM_SBFootSyncNotifies.uasset`
- P4 체크아웃 필요 (작업 전)

## 시작 시점 상태

- AM_SBFootSyncNotifies 는 AM_SBFootStepNotifies 의 **100% 비트 동일 복제본** (compare_blueprints total_diffs=0)
- 사용자가 직접 복제해둔 상태, 분리 작업은 아직 0
- 부모 클래스: `AnimationModifier`
- 변수 42개, 함수 9개, 그래프: EventGraph, ApplyModifier, ProcessFoot, RevertModifier, AddNotify, SetMoveType, SetFootStepSetKey, GetPeakSocketSpeed, GetPeakBoneSpeed, IsFootOnGround

## 분리 계획

| 함수 | 변경 |
|---|---|
| `AddNotify` (18 nodes) | AddAnimationNotifyEvent → AddAnimationSyncMarker + Cast/Setter 제거 + MarkerName 추가 |
| `RevertModifier` (5 nodes) | RemoveAnimationNotifyTrack → RemoveAnimationSyncMarker |
| `ApplyModifier` (83 nodes) | SetMoveType/SetFootStepSetKey 제거 (Task #4, ProcessFoot 분석 후 결정) |
| CDO `NotifyTimeOffset` | -0.09 → 0.0 |

## 컨벤션

- Sync Marker 이름: **`Foot_L` / `Foot_R`** (PC_01 스켈레톤 binary 확인 — 이미 등록됨)
- 컨벤션 근거: UE 표준 (Lyra/GASP), PC_01_Body_001_Skeleton.uasset binary string 확인

## 롤백 방법

1. **P4 우선**: 작업 전 체크아웃했다면 `p4 revert` 또는 unsubmitted 변경 폐기
2. **수동 롤백**: 이 폴더의 `variables_sync.json` / 각 그래프 dump 참고하여 에디터에서 재구성
3. **백업 dump 파일**:
   - `variables_sync.json` — Sync 모디파이어 CDO 변수 default 값
   - `graph_addnotify.json` — AddNotify 그래프 전체 (18 노드)
   - `graph_revertmodifier.json` — RevertModifier 그래프 (5 노드)
   - `graph_applymodifier.json` — ApplyModifier 그래프 (83 노드)
   - `blueprint_info.json` — Blueprint 메타데이터 (변경 전)

## 백업 미포함 (변경 안 함)

- `AM_SBFootStepNotifies` — 분리 작업 중 건드리지 않음. 필요 시 git/p4 히스토리에서 확인
- `ProcessFoot` (291 nodes) — Task #4 분석 시점에서 추가 dump 예정
- `SetMoveType` / `SetFootStepSetKey` / `GetPeakSocketSpeed` / `GetPeakBoneSpeed` / `IsFootOnGround` / `EventGraph` — 변경 계획 없음

## 작업 후 검증 항목

1. 컴파일 OK
2. 변수/함수 카운트 동일 (42/9)
3. AddNotify 노드 수 변경됨 (18 → 약 7~10)
4. RevertModifier 노드 수 비슷 (5 ± 1)
5. CDO NotifyTimeOffset = 0.0
6. 시퀀스 1개 (예: P_Player_Run_Loop_F)에 Apply → `get_sync_markers` 결과에 Foot_L/R 박힘 확인
