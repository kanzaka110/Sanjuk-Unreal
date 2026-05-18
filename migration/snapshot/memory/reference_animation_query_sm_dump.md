---
name: animation-query-sm-dump
description: animation_query 의 get_abp_info / get_state_machines / get_transitions / get_abp_linked_assets 네 액션으로 ABP State Machine 구조를 T3D 파싱 없이 완전 dump 가능.
metadata: 
  node_type: memory
  type: reference
  originSessionId: ea3be7a5-d8f0-4249-af75-76ddb6a92c3d
---

Monolith `animation_query` 네 액션을 묶으면 ABP 의 SM 구조 + transition rule chain 까지 한 번에 받을 수 있다. T3D copy-paste 기반 우회로(dump_animgraph_nodes.py / parse_animgraph_t3d.py) 의 정공법.

**Why:** 2026-05-18 PoC 로 PC_01_ABP 에 실측 (`scripts/analyze_pc01_state_machines.py`).
- `get_abp_info` → skeleton / parent_class / state_machine_count / graph_count(50) / variable_count(149) / graph 이름 enum / interfaces
- `get_state_machines` → SM 1개 (MoveStateMachine) / entry_state / states 12개 (이름+position) / transitions 41개 요약
- `get_transitions` → transitions 41개 + 각각의 **rule_nodes** (K2Node class + title, 한글 코멘트 포함)
- `get_abp_linked_assets` → linked AnimBP 4개 + BlendSpace 1개 + total_dependencies 34

응답 품질 검증:
- rule_nodes 가 "Get IsLockOn" / "Get PrevIsLockOn" / "Not Equal (Boolean)" / "Lock On이 변하는 타이밍은 제외" (코멘트) 등 의도까지 추적 가능
- IsLockOn 변화 timing 제외 / TrjIsCircling 제외 / Pivot OR Start 태그 / Pending Walk Mode 변화 등 SM 진입 조건 자동 catalog

**How to apply:**
- ABP 분석 의뢰 ("PC_01_ABP 상태 어때") 시 `py scripts/analyze_pc01_state_machines.py --asset <path>` 한 번으로 dumps/sm/<NAME>_summary.md + 4개 JSON 받는다.
- IsTransition 정의 작업(2026-05 다음주) 직전 dump 떠서 현 transition rule 카탈로그를 기준선으로.
- T3D 우회로(`dump_animgraph_nodes.py` / `parse_animgraph_t3d.py`) 는 _state_info 의 sub-graph 노드만 필요한 미세 작업 외엔 안 써도 됨 (archive 후보).
- 다른 ABP (PC_01_AnimLayer_IK, PC_OverlayLayerBlending 등) 진단에도 동일 패턴 통함.

한계:
- `get_state_info` 가 GroundMoving 처럼 BlendStack 기반 state 는 단일 `AnimGraphNode_StateResult` 만 보여줌 → BlendStack 안쪽 노드는 별도 (`get_nodes` with graph_name)
- transition 의 from 이름이 conduit/inline ("Re-Transit to GroundMoving") 인 경우, 어느 source state 의 외향 transition 인지 별도 매핑 필요. T3D 의 source state 정보가 여기엔 없음.

관련 메모리: [[pc01-abp-chain]], [[pc01-anim-rewind-recorder]], [[absorption-candidates-2026-05-18]], [[monolith-log-capture-limit]].
