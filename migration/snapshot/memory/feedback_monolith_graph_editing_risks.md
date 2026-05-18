---
name: Monolith로 AnimBP 그래프 편집 시 함정
description: PC_01_ABP에 Event BlueprintUpdateAnimation 추가로 Anim Preview 무한 루프 → P4 revert로 복구한 경험. 다음 시도 시 주의점.
type: feedback
originSessionId: c0b37efc-71b6-4348-a2e2-afba5093f18e
---
AnimBlueprint의 그래프를 Monolith `blueprint_query`로 편집할 때 조심할 3가지.

**Why:** 2026-04-20 PC_01_ABP에 계단 감지 로직(새 이벤트 + 22노드 함수 + 변수 6개) 추가 → Anim Preview에서 `Set JumpPrevCount` 무한 루프 감지 → 에디터 프리즈 → P4 revert로 완전 원복.

**How to apply:**

1. **AnimBP에 `Event BlueprintUpdateAnimation` 추가 금지 (기존에 없으면)**
   - Anim Preview 액터는 GetOwningActor가 불완전해서 새 이벤트가 예상 못한 코드 경로 탐. UpdateVariables 같은 기존 함수에서 런어웨이 루프 트리거 가능.
   - 대안: `BlueprintUpdateAnimation` 대신 **PropertyAccess 바인딩** 또는 **이미 존재하는 UpdateVariables 함수 확장**.

2. **UPROPERTY struct는 Python API로 영속화 안 됨**
   - `anim_node.get_editor_property("pelvis_settings")` 로 받은 struct는 **by-value 복사본**.
   - set_editor_property로 써도 in-memory만 반영, 저장/컴파일에 안 박힘.
   - `FFootPlacementPelvisSettings` 같은 struct는 **에디터 Details에서 직접 타이핑**만 확실.

3. **대규모 그래프 추가는 P4 check-in 상태에서 단계별로**
   - 변수 추가 → 컴파일 확인 → 함수 추가 → 컴파일 확인 → 이벤트 추가 → **이 단계부터 매우 위험**.
   - 이상 징후(preview 느려짐, 로그 경고) 즉시 p4 revert. 쌓아두면 복구 불가.

**복구 순서:**
1. 에디터 Anim Preview 창 먼저 닫기 (에러 스팸 멈춤)
2. Ctrl+S 저장 시도
3. 반응 없으면 Task Manager End Task (**PC 전원 내리지 말 것**)
4. `p4 revert <uasset_path>` 로 depot 상태 복구
5. 파일 read-only(r--) 확인 + 바이너리 grep으로 흔적 없음 확인

**안전한 대안 (다음 시도 시):**
- 계단 감지 로직은 **기존 `UpdateVariables` 함수 내부에 추가** (277 노드라 많지만 새 이벤트 없음)
- 또는 **C++로 SBActorAnimInstance 확장** (BP 편집 리스크 없음, 엔진팀 협의 필요)
- 또는 가장 단순히 **FootPlacement 노드 Alpha를 CMC의 bUseRVOAvoidance 같은 기존 bool로 수동 토글**

**2026-04-20 2차 실패 추가 경험:**
- TSU에 직접 인라인 / UpdateVariables 확장 **둘 다 실패** — 같은 Set JumpPrevCount 무한루프 재발
- BP 컴파일 자체가 Content Browser 썸네일 + Anim Preview 재평가 트리거 → 기존 버그 깨움
- **어떤 Monolith BP 수정도 PC_01_ABP에 대해 이 루프 트리거**. Monolith로 PC_01_ABP 수정 시도 자체를 피할 것
- 해결 전제: `Set JumpPrevCount` 내부 루프 버그 규명 필요 (SBCharacter 캐스트 실패 시 터짐)
- 로그 시그니처: `PIE: Error: 무한 루프가 감지되었습니다. 블루프린트: PC_01_ABP 함수: Set JumpPrevCount`
