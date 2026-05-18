---
name: ControlRig 그래프 add_node → Monolith 서버 다운
description: PC_01_CtrlRig_FootClamp 작업 중 Monolith add_node(VariableGet)가 ControlRig 그래프에서 서버를 다운시킴. ControlRig wiring은 수동 또는 copy_nodes 권장.
type: feedback
originSessionId: 64ea9e0b-3b30-498c-8fcc-ec04da2eec36
---
ControlRig 그래프에 `blueprint_query.add_node(VariableGet)` 호출 시 Monolith 서버 충돌 (2026-04-30, FootClamp 작업 중).

**Why:** ControlRig(RigVM 기반)는 `URigVMEdGraphNode` 노드 타입을 사용. 일반 Blueprint의 K2Node 핸들러가 ControlRig 그래프에서 노드를 만들려다 크래시. Monolith `add_node`는 Blueprint용이므로 ControlRig에는 적용 불가.

**How to apply:**
- ControlRig 그래프 wiring은 Monolith `add_node` / `connect_pins` 사용 금지
- CDO 변수 값 변경 (`set_pin_default`, `add_variable`)은 OK (이전 세션에서 RotationOrder 수정 성공)
- 그래프 노드 추가/연결은 에디터에서 수동 또는 `copy_nodes`로 다른 어셋에서 복제
- 실행 전 ControlRig 여부 확인: 에셋 경로가 `/Rig/`에 있으면 ControlRig일 가능성 높음
