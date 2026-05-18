---
name: sb2-python-plugin-disabled
description: SB2 빌드 (UE 5.7.4 custom) 에 PythonScriptPlugin 이 비활성화. runreal MCP / monolith.scripting.execute_script(python) / UE Python reflection 우회 모두 차단.
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ea3be7a5-d8f0-4249-af75-76ddb6a92c3d
---

SB2 빌드에서 `monolith.scripting.execute_script(script_type="python", ...)` 호출 시:
> "Python scripting not available. Enable PythonScriptPlugin in the plugin manager."

**Why:** 2026-05-18 PoC 시도. PC_01 EvieAnimChooser ResultsStructs protected 우회를 monolith.scripting.execute_script 로 시도했으나 즉시 거부. runreal MCP(`editor_run_python`)도 동일 의존성이라 같이 차단.

**영향 — 메모리 [[reference-monolith-animgraph-editing-limits]] 의 5가지 한계 중 다수가 영향 받음**:
- Chooser ResultsStructs protected → Python reflection 우회 불가
- State Machine sub-graph → 동일
- Enum class UObject ref 바인딩 → 동일
- Array polymorphism wildcard 미해결 → 동일
- Function metadata BlueprintThreadSafe → 동일

= 메모리 [[reference-runreal-python-bypass]] 의 우회 패턴 **현재 적용 불가**. 플러그인 활성화 후에야 작동.

**How to apply:**
- 사용자 작업 (사용자가 직접 수행):
  1. UE 에디터 → Edit → Plugins → "Python" 검색
  2. **Python Editor Script Plugin** 활성화 (Enabled 체크)
  3. (선택) **Editor Scripting Utilities** 도 확인
  4. UE 에디터 재시작
  5. monolith.scripting.execute_script 또는 runreal MCP 재시도
- SB2 팀 정책 확인 필요 — 빌드 기본 비활성화가 의도인지, 단순 미설정인지
- 활성화 어렵다면 우회 정공법:
  - .uasset binary scan (사내 SB2AssetParser 가 이 영역)
  - Python 없이 가능한 영역은 UnrealClaude HTTP 가이드 (`cache/ue57_contexts/`) + Monolith 직접 액션

**대안 (Python 없이 가능):**
- ChooserTable ResultsStructs 의 셀 값 추정 = 사내 SB2AssetParser MCP `sb2_asset_properties` (메모리 [[reference-sb2-internal-mcps]])
- 그러나 SB2AssetParser 도 미등록 ([[project-sb2-internal-mcp-pending]]) — P4 sync + 사내 서버 가동 대기

관련 메모리: [[reference-runreal-python-bypass]], [[reference-monolith-animgraph-editing-limits]], [[reference-sb2-internal-mcps]], [[project-sb2-internal-mcp-pending]].
