---
name: animgraph-node-editing
description: animation_query 의 add_anim_graph_node / connect_anim_graph_pins / add_state_to_machine 등 AnimGraph 편집 액션 실측 결과. IsTransition gate 구현 패턴.
metadata: 
  node_type: memory
  type: reference
  originSessionId: ea3be7a5-d8f0-4249-af75-76ddb6a92c3d
---

## 실측 결과 (2026-05-18 PoC, 임시 ABP `/Game/_Test/Test_AnimGraphEdit_ABP`)

### add_anim_graph_node 가 지원하는 node_type (정확)
- `SequencePlayer` — anim_asset 인자로 시퀀스 자동 set. 핀: `Pose` (Output)
- `BlendSpacePlayer` — anim_asset 으로 BlendSpace
- `TwoWayBlend` — 핀: `A` (Input pose), `B` (Input pose), `bAlphaBoolEnabled` (bool), `Alpha` (real), `AlphaCurveName` (name), `Pose` (Output)
- `BlendListByBool` — 핀: `BlendPose_0`/`BlendPose_1` (Input pose), `BlendTime_0`/`BlendTime_1` (real), `bActiveValue` (bool), `Pose` (Output)
- `LayeredBoneBlend`, `MotionMatching` (PoC 미검증, 스키마에만 존재)

K2Node 일반 노드는 `blueprint.add_node` 영역.

### connect_anim_graph_pins
- 응답: `{asset_path, source_node, source_pin, target_node, target_pin, compiled}` — `compile=true` (기본) 이면 즉시 컴파일.
- 핀 이름은 대소문자 정확히 (`Pose` / `Result` / `A` / `B` / `BlendPose_0` 등).
- compile success 시 `compiled: true` 응답.

### State Machine 신규 생성 — 사실상 불가
- animation_query 에 SM 생성 액션 없음.
- `blueprint.add_node` generic fallback 으로 `AnimGraphNode_StateMachine` 추가 가능 **하지만 invalid**:
  ```
  title="오류: 그래프 없음\n스테이트 머신"
  warning="Created via generic K2Node fallback — node may require additional configuration"
  ```
- 사용자가 에디터에서 우클릭 → Add State Machine 으로 만들어야 정상.
- 결과: **신규 SM 만들기는 사용자 수동, 기존 SM 편집만 Monolith 영역**.

### add_state_to_machine / add_transition / set_transition_rule (스키마만)
- 기존 SM 위에서만 의미. machine_name 인자 필수.
- `set_transition_rule(variable_name=...)` 은 **boolean variable 1개** 만 wire 가능 → 기존 rule chain (AND/OR/Get/Comparison/Comment) 다 **덮어써져 사라짐**.
- 즉 IsTransition 같은 게이트를 transition 에 추가하려면 set_transition_rule 사용 시 기존 룰 전부 잃음. 추가 wiring 은 blueprint.add_node 로 별도 노드 만들고 사용자가 에디터에서 rule graph 안에 합쳐야 함.

### set_state_animation
- 고수준 shortcut. 안에서 SequencePlayer/BlendSpacePlayer 자동 spawn + Result wire.
- `clear_existing=true` 기본 → 기존 player 노드 제거. 위험.

## IsTransition gate 구현 권장 패턴 (PC_01_ABP 다음주 작업)

State Machine 자체 편집 한계가 명확하므로, **IsTransition 변수로 분기하는 AnimGraph 합성 노드** 패턴 권장:

```
AnimGraph (top-level, AnimGraphNode_Root_0 의 입력 측):

  [Smooth Chain 출력 (기존)]──────┐
                                  │
  [Transition 처리 chain]─────────┤
                                  │
                                  ▼
                          BlendListByBool
                          ├─ BlendPose_0 ← Smooth chain
                          ├─ BlendPose_1 ← Transition chain
                          ├─ bActiveValue ← VariableGet(IsTransition)
                          ├─ BlendTime_0 = 0.0 (즉시)
                          ├─ BlendTime_1 = 0.0
                          └─ Pose ──→ Root.Result
```

이 패턴이 좋은 이유:
1. State Machine 내부 transition rule 안 건드림 (덮어쓰기 위험 회피)
2. add_anim_graph_node + connect_anim_graph_pins + blueprint.add_node(VariableGet) 모두 Monolith 액션
3. compile 즉시 검증 가능
4. 잘못되면 remove_node 로 분기만 제거하고 smooth chain 복귀

대안 (덜 권장): SM 안에 별도 state 추가 + set_transition_rule(IsTransition). 단점은 기존 transition rule 손실 + state 안의 inner graph 는 별도 wiring 필요.

## How to apply
- IsTransition 작업 시작 직전 `analyze_pc01_state_machines.py` 로 기준선 dump.
- BlendListByBool 패턴으로 분기 추가 (add_anim_graph_node → connect_anim_graph_pins → blueprint.add_node(VariableGet) → connect).
- save 실패 P4 잠금은 동일 ([[project-pc01-psd-gmt-continuing-bias]] 학습) — 사용자 Ctrl+S 안내.
- SM transition rule 직접 편집 필요시 사용자가 에디터에서 작업.

관련 메모리: [[reference-monolith-animgraph-editing-limits]], [[reference-animation-query-sm-dump]], [[pc01-session-end-2026-05-15]], [[absorption-candidates-2026-05-18]].
