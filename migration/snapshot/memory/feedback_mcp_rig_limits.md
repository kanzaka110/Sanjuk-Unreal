---
name: MCP 리깅/시뮬레이션 디테일 작업 한계
description: Monolith/ChiR24 MCP로 가능한 UE5 작업 범위 — 그래프 기반은 가능, 뷰포트 인터랙션 필요 작업은 불가
type: feedback
---

프로덕션 수준 Control Rig를 MCP로 처음부터 구축하는 것은 불가능. 단순 FK는 되지만 CR_Mannequin_Body(220노드, 172 커스텀 함수) 수준은 복제 후 수정이 현실적.

**가능:** Blueprint 그래프, AnimBP State Machine, 머티리얼, 나이아가라, AI(BT/ST/EQS), GAS
**불가능:** Control Rig 프로덕션 IK, Cloth 시뮬레이션 파라미터, Weight 페인팅, 시퀀서 키프레임 세부

**Why:** RigVM 커스텀 함수 중첩 구조는 API가 부족, 에디터 뷰포트 인터랙션(페인팅/드래그) 작업은 MCP로 대체 불가.
**How to apply:** 복잡한 리그/시뮬레이션은 "복제 후 수정" 전략 사용. 노드 그래프 기반 시스템만 처음부터 AI 구축 시도.
