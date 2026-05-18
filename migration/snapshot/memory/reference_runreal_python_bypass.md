---
name: runreal-python-bypass
description: "runreal `editor_run_python` 으로 Monolith protected/sub-graph 한계를 UE Python reflection 으로 우회. ChooserResultsStructs / State Machine sub-graph / Function metadata 접근 가능."
metadata: 
  node_type: memory
  type: reference
  originSessionId: ea3be7a5-d8f0-4249-af75-76ddb6a92c3d
---

runreal MCP 의 `editor_run_python` 은 UE 안에서 `unreal` Python API 를 임의 코드로 실행한다. Monolith blueprint_query / animation_query 가 reflection 제약으로 못 다루는 영역을 대부분 우회할 수 있다.

**Why:** 2026-05-18 시너지 점검 중 발견. runreal Tutorial 06 "반드시 import unreal 로 시작 / 주석 금지 / print() JSON 출력" 규칙. Monolith 한계 ([[reference-monolith-animgraph-editing-limits]]) 와 매핑.

## 우회 가능 영역 (실측은 UE 가동 시)

| Monolith 한계 | runreal Python 우회 | 비고 |
|---|---|---|
| Chooser `ResultsStructs` protected 직렬화 `{}` | `chooser.get_editor_property("ResultsStructs")` → 직접 iterate, 각 entry 의 `AnimationAsset` / `OutputObject` 접근 | PoC 스크립트: `scripts/runreal_chooser_inspect.py` |
| State Machine sub-graph 접근 불가 | `abp.get_blueprint_generated_class()` → AnimGraph traverse → `UAnimStateMachineNode` 등 reflection | 한 단계 더 복잡, 5.7 API 확인 필요 |
| Enum class UObject ref 바인딩 불가 (set_pin_default 실패) | Python 에서 `unreal.load_object(None, "/Script/Mod.EClass")` 후 노드의 enum pin 직접 set | UE 5.7 의 K2Node API 노출 범위 확인 |
| Function metadata BlueprintThreadSafe 설정 불가 | `func.set_metadata("BlueprintThreadSafe", "true")` 또는 `K2Schema` 호출 | UE Python 에서 UFunction metadata API 확인 필요 |
| Array polymorphism wildcard 미해결 | Python 에서 `K2Node_CallArrayFunction` 직접 spawn → array pin wildcard 자동 resolve | Monolith add_node 는 일반 K2Node_CallFunction 으로 만듦 |

## 실행 패턴

호스트 (claude-code) 에서:
```
mcp__unreal-mcp__editor_run_python(payload=<Python source>)
```
- Payload 는 `scripts/runreal_chooser_inspect.py` 같은 빌더로 생성
- 응답은 stdout (print) — JSON 으로 출력하면 파싱 용이
- 주석 (`#`, `'''`) 금지 — 모두 변수/문자열로 인코딩

## How to apply

- Monolith 가 protected / 빈 응답 / sub-graph 에러 던지면 → runreal Python 으로 즉시 우회 시도
- 새 우회 패턴 검증 시 `scripts/runreal_<영역>_inspect.py` 빌더 추가 → 메모리에 결과 기록
- UE 미가동 시 호스트에서 payload 생성/검증만 (dry-run). PoC 는 UE 가동 후 실측.
- runreal 의 stdio 통신은 UE 에디터 안의 Python 인터프리터에 의존 — 에디터 미가동 시 MCP 자체 미응답.

## 한계 (runreal 도 못하는 영역)

- UE 안 Python API 자체에 노출 안 된 영역 (private C++ 메서드, 모듈 internal)
- P4 잠금 save 는 runreal 도 동일 — `unreal.EditorAssetLibrary.save_asset(...)` 가 P4 check out 안 시도
- 너무 무거운 작업 (대량 reflection traverse) 은 UE 가 hang 위험

관련 메모리: [[reference-monolith-animgraph-editing-limits]], [[absorption-candidates-2026-05-18]], [[reference-ue57-source-cache]].
