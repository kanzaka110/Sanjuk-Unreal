---
name: UE 기능/옵션 설명 시 한글 UI명 사용
description: 언리얼 에디터 기능, 옵션, 파라미터 설명 시 한글화된 UI 이름으로 안내. 영문명은 괄호 병기.
type: feedback
originSessionId: abee917a-80bb-4cf4-a80c-e01a5e7ce6da
---
**규칙**: UE 기능/옵션/파라미터 설명 시 **한글 UI 이름을 기본**으로 사용.

**Why:** SB2 빌드는 한글화 설정이 되어 있어 영문명만 부르면 에디터에서 못 찾을 수 있음. 사용자가 직접 요청 (2026-04-16).

**How to apply:**
- 파라미터명: "선형 강성 (LinearStiffness) = 300" 식으로 한글 먼저, 영문 괄호 병기
- 메뉴/옵션: "편집 > 프로젝트 설정 (Edit > Project Settings)" 식
- 노드명: "발 배치 (Foot Placement)", "다리 IK (Leg IK)" 식
- 이미 reference_foot_placement_source_5_7.md에 한/영 매핑 일부 있음 — 새로운 매핑 발견 시 해당 파일 또는 별도 reference에 축적
