# Script Archive

완료되었거나 시도 후 접힌 실험 스크립트 보관소. 재참조용으로만 유지.

## `legik_stair/` — LegIK temporal smoothing + 계단 시도

**배경**: 계단 오르내림에서 LegIK 시간축 smoothing 시도 (TwoBoneIK + LegSmooth).
**결과**: 엔진 한계로 안정 smoothing 불가 — 포기 (커밋 `451fec6`).
**관련 메모리**: `project_pc01_anim_debugging.md`

## `fp_stair_detect/` — FootPlacement 계단 감지 + Inertialization 탐색

**배경**: FootPlacement가 계단 step를 인지하도록 감지 로직 스크립트 + Inertialization 노드 위치 탐색.
**결과**:
- 계단 감지는 실용성 낮아 아이디어만 정리 (커밋 `77b3b47`)
- Inertialization 위치 탐색 결과는 메모리화됨 (`project_pc01_abp_chain.md`)
- CDO 덤프는 개선판 `scripts/dump_footplacement_params.py` 가 대체

## 복원 방법

필요 시 `git mv scripts/_archive/<folder>/<file>.py scripts/` 로 복원.
