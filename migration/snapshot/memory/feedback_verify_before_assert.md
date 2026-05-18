---
name: UE 단정 답변 전에 공식 샘플/문서 확인
description: "GASP는 둘 다 쓰는데?" 피드백 이후, UE 기능의 "일반 원칙"을 주장할 때는 공식 샘플/문서로 검증 후 답변.
type: feedback
originSessionId: 38491534-e53a-4fee-be48-740ab304fcba
---
**규칙**: UE 노드/기능의 일반 원칙을 주장할 때는 공식 샘플(GASP) 또는 Epic docs로 확인 후 답변.

**Why:** 2026-04-15 세션에서 "FootPlacement와 LegIK 둘 다 쓰면 충돌 → LegIK 끄라"고 조언했으나, 사용자가 "GASP에선 둘 다 쓰는데?"라고 반박. 실제로 GASP는 두 노드를 순차 사용 (FootPlacement가 고수준 배치, LegIK가 본 단위 마무리) — 제 조언이 틀렸음.

**How to apply:**
- "X와 Y를 동시에 쓰면 안 된다" 같은 **일반화 주장 전에**: GASP 프로젝트에서 실제 사용 여부 확인 (사용자 PC에 이미 설치됨: `C:\Users\SHIFTUP\Documents\Unreal Projects\GameAnimationSample`)
- Epic 공식 샘플에 있는 패턴은 "틀렸다"고 단정하지 말 것. "충돌 가능성" 정도로 표현하고 실제 순서/설정 확인 방향으로 유도.
- 사용자가 공식 문서/샘플 인용해서 반박하면 즉시 인정 + 원인을 다른 쪽에서 재탐색.
