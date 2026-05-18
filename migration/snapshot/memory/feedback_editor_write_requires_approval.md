---
name: 에디터 데이터 수정/생성/제거는 사전 승인 필수
description: UE 에디터 에셋(BP/ABP/PSD/Chooser/Montage/Sequence 등) 변경 작업은 사용자가 명령했을 때만 또는 사전 의사 확인 후 진행
type: feedback
originSessionId: 000356af-f6ab-4220-891c-ca3825b31e2a
---
UE 에디터 데이터를 **수정/생성/제거**하는 일은 다음 중 하나일 때만 진행한다:
1. 사용자가 명시적으로 명령했을 때
2. 진행해도 되는지 사용자에게 먼저 의사를 물어 **승인을 받은 이후**

**Why:** 에셋 변경은 P4/되돌리기 비용 + 다른 에셋 의존성 + 런타임 영향이 크고, 한 번 잘못 건드리면 복구가 어려움. 사용자가 2026-04-27 "중요한 문제"로 명시.

**How to apply:**

**진행 전 승인 필요 (write 액션):**
- `add_database_sequence` / `remove_database_sequence` / `set_database_sequence_properties`
- `rebuild_pose_search_index` (재빌드도 변경 행위)
- `create_*` / `add_*` / `remove_*` / `set_*` 류 모든 Monolith 액션
- `add_anim_graph_node` / `connect_anim_graph_pins` / `set_pin_default_value`
- `add_state_to_machine` / `add_transition` / `set_transition_rule`
- ChooserTable / BlueprintGraph / ABP / Montage / Sequence / PSD / Schema 모든 변경
- save_asset, P4 체크아웃/체크인
- 에셋 신규 생성, 복제, 삭제, 이름변경

**승인 없이 진행 가능 (read-only):**
- `get_*` / `list_*` / `inspect_*` / `dump_*`
- `monolith_status` / `monolith_discover`
- 파일 Read / Grep / Glob / git status·log·diff
- 분석 스크립트 작성(에디터 변경 없는 것)

**제안 형식 권장:**
- "이 액션을 실행하면 X가 Y로 바뀝니다. 진행할까요?"
- 변경 범위(어떤 에셋, 어떤 필드, 이전 값 → 이후 값) 명시
- 되돌리기 방법 함께 안내
- 사용자 "ㅇㅇ"/"진행"/"해줘" 등 명확한 응답 후에만 실행

**예외:** 사용자가 한 메시지에서 "X해줘"라고 명시한 경우는 즉시 실행 가능 (그 명령에 한정).
