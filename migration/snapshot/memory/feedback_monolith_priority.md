---
name: Monolith 최우선순위
description: MCP 도구 사용 시 Monolith가 항상 최우선, UnrealClaude는 보조적으로만 사용
type: feedback
---

에디터 제어가 필요한 모든 작업은 Monolith를 먼저 사용한다. UnrealClaude는 Monolith로 불가능한 작업에만 사용.

**Why:** 사용자가 Monolith를 메인 도구로 지정. 1,125 액션으로 커버리지가 훨씬 넓고 안정적.

**How to apply:**
- 액터, BP, 애니메이션, 머티리얼, 레벨 등 에디터 작업 → Monolith
- UE5.7 API 문서 조회, C++ 코드 작성/수정 → UnrealClaude (보조)
- 기능이 겹치는 경우 항상 Monolith 우선
