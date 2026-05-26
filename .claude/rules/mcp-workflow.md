# MCP 워크플로우 규칙

## 도구 우선순위 (반드시 준수)

1. **Monolith** (localhost:9316) — 에디터 제어 전체. 항상 최우선 시도
2. **UnrealClaude** (localhost:3000) — UE5 API 문서 컨텍스트, C++ 참조용
3. **runreal** (stdio) — Python 스크립트 자동화, 배치 작업

## Monolith 도메인 (v0.12.1, 893 액션 — 2026-05-18 measured)

`monolith_discover()` 응답 기반 — 갱신은 `py scripts/save_discover_snapshot.py`.

| 도메인 | 액션 수 | 용도 |
|------|---:|------|
| ai | 218 | BT, Blackboard, StateTree, EQS, Perception, Mass, Smart Object, navmesh |
| mesh | 197 | 레벨 디자인, 공간 쿼리, 프로시저럴, blockout, prefab, LOD, navmesh |
| animation | 116 | AnimSequence, Montage, BlendSpace, ABP, SM, PSD/PoseSearch, Control Rig |
| niagara | 97 | 파티클, 이미터, 다이나믹 인풋, NPC, Effect Type |
| blueprint | 88 | 그래프 편집, 변수, 노드, CDO, 컴파일 |
| material | 57 | 머티리얼 그래프, 함수, 인스턴스 |
| ui | 42 | 위젯 블루프린트, UI 템플릿, 접근성 |
| editor | 25 | 빌드/로그/scene preview/console command/asset CRUD |
| character | 15 | 캐릭터 데이터, MovementParams, stats table |
| source | 11 | UE 소스 read/find_references/callers/callees |
| enhanced_input | 8 | InputAction, MappingContext, Trigger, Modifier |
| config | 6 | INI 설정 resolve/explain/diff |
| project | 6 | search/find_references/dependencies |
| monolith | 4 | discover, status, update, reindex (메타) |
| scripting | 3 | execute_script, history, cleanup |

**Optional (not installed):** combograph (ComboGraph 플러그인 필요, Fab marketplace)

**참고:** 이전 표의 MonolithGAS(130) / MonolithLogicDriver(66) 도메인은 v0.12.1 SB2 빌드에 **없음**.

## SB2 차단/주의 액션 (재시도 금지)

SB2 licensee 빌드 특성상 아래 액션은 호출해도 실패하거나 위험하다. 매 세션 재발견하지 말 것.

### 🔴 차단 (호출 금지 — 실패 확정)
| 액션 | 이유 | 대체 |
|------|------|------|
| `source.*` (11액션) | Engine/Source DB 없는 licensee 빌드. `trigger_project_reindex`도 무효 | `cache/ue57/` 로컬 헤더 + 사내 CodeIndexClient MCP |
| `scripting_query("execute_script", python)` | PythonScriptPlugin 비활성 (SB2.uproject 미등록) | runreal `editor_run_python` (별 프로세스) 또는 사용자 수동 실행 |

### 🟡 한계 (부분만 가능)
| 대상 | 한계 | 비고 |
|------|------|------|
| Chooser `ResultsStructs` | protected — 셀별 결과 시퀀스 매핑 불가 | 컬럼 메타/row count/disabled까지만. 정밀 매핑은 에디터 수동 inspect |
| State Machine transition rule | sub-graph 미접근 | `get_transitions`로 rule 존재까지만 |
| `save_asset` | P4 체크아웃 필요 시 실패 | 수동 저장 / P4 체크아웃 선행 |

### ⚠ read-only도 무조건 안전하지 않다
- **경로 sanitize 필수** — `//Game/...` 이중 슬래시는 read-only 호출이어도 **에디터 즉시 fatal crash** (2026-05-19 2회 발생). 모든 인풋 단일 슬래시 검증.
- **`monolith_discover` 전체 / `getall` 100+ 금지** — 토큰 폭발. 항상 **targeted query**(asset_path 한정, property_names 명시)로.
- **결과 크기 제한** — `get_cdo_properties` 전체 호출 금지(응답 중단), `get_graph_summary` 풀 dump 대신 `get_node_details` 노드 ID 명시.

### 승인 전 금지 (write 액션)
`create_* / add_* / remove_* / set_* / connect_* / disconnect_* / save_asset / rebuild_pose_search_index` 및 Chooser·PSD·ABP 변경은 **사용자 승인 전 실행 금지**. (Inspector는 read-only만, 변경은 Tuner가 승인 후)

## 액션 패턴

```
# 조회: list → inspect 순서
animation_query("list_sequences", ...)
animation_query("inspect_abp", ...)

# 생성: create → configure
animation_query("create_montage", ...)
animation_query("add_notify", ...)

# 벌크 생성: JSON spec 활용
build_behavior_tree_from_spec(spec_json)
build_state_tree_from_spec(spec_json)
```

## 실패 처리 순서

1. Monolith 연결 실패 → UE 에디터 실행 확인 → `/recover`
2. 액션 실패 → 에셋 경로 확인 (Copy Reference) → 재시도
3. 인덱싱 미완료 → "LogMonolith" 로그 확인 → 대기 후 재시도
4. Monolith 불가 시 → runreal Python 스크립트로 폴백
5. MCP 전체 불가 시 → 문서/가이드 기반 수동 안내

## 작업 전 필수 확인

- `/doctor`로 MCP 전체 상태 점검 (첫 작업 시)
- Monolith 포트 9316 응답 확인 (PreToolUse 훅이 자동 수행)
- 에셋 경로는 항상 에디터에서 Copy Reference로 정확한 경로 취득
