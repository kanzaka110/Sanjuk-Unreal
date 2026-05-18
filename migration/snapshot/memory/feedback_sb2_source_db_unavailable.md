---
name: sb2-source-db-unavailable
description: "SB2 환경에서 monolith source.* 11 액션 모두 \"Engine source DB not available\" 거부. Engine/Source 없는 licensee 빌드 영향. 사내 CodeIndexClient MCP 가 대체 경로."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ea3be7a5-d8f0-4249-af75-76ddb6a92c3d
---

Monolith `source_query` (11 액션: read_source / find_references / find_callers / find_callees / search_source / get_class_hierarchy / get_module_info / get_symbol_context / read_file / trigger_reindex / trigger_project_reindex) 가 SB2 환경에서 **전부 `Engine source DB not available` 응답**.

**Why:** 2026-05-18 측정. SB2 가 licensee-modified UE 5.7.4 커스텀 빌드 — `Engine/Source` 디렉토리 없음 ([[project-sb2-engine]]). source.* 도메인은 indexed engine source DB 의존. trigger_project_reindex 호출 시 "loads existing engine symbols, indexes project Source/ and Plugins/" 라 명시 — Engine symbols 가 없으면 project 인덱싱도 활성 안 됨.

trigger_project_reindex 호출 결과:
```
"Project source indexing started (incremental). This runs in the background — check editor log for progress."
```
→ 15초 후 find_callers/get_module_info 재시도 → 여전히 "Engine source DB not available"

**영향:**
- Monolith source.* 11 액션 = SB2 에서 사용 불가
- UE5 cross-ref / caller chain / class hierarchy 정보 필요 시 다른 경로 필수

**대체 경로 (우선순위):**
1. **cache/ue57/ 13 헤더 + ue57_contexts/ 13 가이드** ([[reference-ue57-source-cache]]) — 오프라인 즉답, 영역 한정
2. **사내 CodeIndexClient MCP** ([[reference-sb2-internal-mcps]], [[project-sb2-internal-mcp-pending]]) — UE5 229,959 파일 / 3,566,443 심볼 인덱스. **현재 미등록 (P4 sync 필요)**. 등록 시 완전한 cross-ref 가능
3. **GitHub raw URL + gh api** (`https://raw.githubusercontent.com/EpicGames/UnrealEngine/5.7/...`) — Engine source 가 EpicGames private 리포에 있으면 가능. 캐시 보충
4. **사내 BlueprintIndexer MCP** — Widget BP + C++↔BP 호출만 (좁은 영역)

**How to apply:**
- Monolith source.* 호출 시도 금지 — 즉시 거부. 시간 낭비
- UE5 cross-ref 의뢰 시 우선 cache/ue57 Read → 부족하면 사내 CodeIndexClient 등록 후 진행 권장
- 사용자가 사내 MCP P4 sync 받으면 source.* 흡수 시도 영역이 완전히 풀림

**검증 시점:**
- SB2 빌드에 Engine/Source 가 추가되거나 (licensee 정책 변경), 사내 CodeIndexClient 등록 후 → 본 한계 재검증

관련 메모리: [[project-sb2-engine]], [[reference-ue57-source-cache]], [[reference-sb2-internal-mcps]], [[project-sb2-internal-mcp-pending]], [[absorption-candidates-2026-05-18]].
