---
name: PC_01은 Phase curve 기반이라 Sync Group 불필요
description: SB2 PC_01의 Locomotion phase 동기화는 PoseSearchFeatureChannel_Curve가 anim curve "Phase"를 트래킹하는 구조. Sync Group/Marker 추가는 중복.
type: project
originSessionId: 08caf478-3332-4b2f-a786-11941d7ec8e5
---
# PC_01 Phase 동기화 구조

## 사실 (2026-04-29 덤프 확인)

PC_01 Locomotion 409 AnimSequence + 7개 PoseSearch DB + 4개 Schema 분석 결과:

- **Sync Marker: 0개** (모든 클립)
- **PoseSearch Schema 4종**:
  - `PSS_SM_Idles` — Trajectory 기반, phase 무관
  - `PSS_SM_LocoLoops` — `PoseSearchFeatureChannel_Curve`가 anim curve **"Phase"** 트래킹
  - `PSS_SM_LocoTransitions` — 동일 (Curve "Phase")
  - `PSS_SM_Jump` — Trajectory 기반, phase 무관
- 정식 `PoseSearchFeatureChannel_Phase` 클래스는 **0개 사용** — SB2 자체 컨벤션

발 정보 소스: `AN_SBFootStepNotify` (Footstep Left/Right 트랙) + 파일명 `_Lfoot/_Rfoot` suffix.

## Why
SB2는 정식 Phase 채널 클래스 대신 anim curve "Phase"를 만들어 Curve 채널로 매칭. 이미 작동하는 phase sync 시스템 존재.

## How to apply
- **Sync Group / Sync Marker 추가 검토 → 거절 사유**: LocoLoops/LocoTransitions에 Sync Group 추가하면 Curve "Phase" 매칭과 **중복/충돌** 가능. Idles/Jump는 phase 무의미.
- 발 슬라이드 / 위상 점프 증상 발생 시 의심 순서:
  1. **개별 클립의 "Phase" curve 누락/비정상** (간헐적 증상의 가장 유력한 원인)
  2. Phase curve 값 스케일 (0~1 정규화 여부)
  3. PSD 인덱싱 상태
  4. BlendStack 옵션
- "Phase" curve는 SB2가 자체 생성한 것으로 추정 (UE 5.7 표준 자동 생성과 이름 다를 수 있음). 일괄 생성 스크립트 존재 여부는 미확인.

## 산출물 위치
- `dumps/sync_groups/pc01_psd_schema_channels.md` — Schema 4종 채널 구성
- `dumps/sync_groups/schema/PSS_SM_*.json` — Schema raw
- `dumps/sync_groups/pc01_locomotion_sync_markers_2026-04-29.md` — Sync Marker 0개 확인
- `dumps/sync_groups/_anim_to_psd.json` — 클립↔PSD 매핑

## 결정 (2026-04-29)
사용자가 Sync Group 적용 시도 후 모두 원복. 향후 PC_01에서 Sync Group/Marker 작업은 새 근거 없으면 제안하지 않음.
