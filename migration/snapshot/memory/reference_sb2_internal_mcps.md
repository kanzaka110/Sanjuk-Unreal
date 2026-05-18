---
name: sb2-internal-mcps
description: SB2 사내 Confluence 에서 발견한 사내 MCP 3개 (SB2AssetParser / CodeIndexClient / BlueprintIndexer). 모두 미등록 상태. 등록 시 Monolith 한계 대부분 보완.
metadata: 
  node_type: memory
  type: reference
  originSessionId: ea3be7a5-d8f0-4249-af75-76ddb6a92c3d
---

SB2 Confluence space (`SB2`, id=250282003) 하위 "MCP" 폴더(1237549058) 에서 발견. 2026-05-18 확인 — 현재 `.mcp.json` 에 등록 안 됨. 등록만 하면 Monolith 한계 영역 대부분 해소.

## ① SB2AssetParser MCP — UE 미가동 시 .uasset 직접 파싱

- 페이지: https://shiftupcorp.atlassian.net/wiki/spaces/SB2/pages/1577353472/SB2AssetParser+MCP (2026-05-04 작성)
- 설치: `//depot/main/Program/Tools/MCP/SB2AssetParser/Setup-SB2AssetParser.bat`
- 필요: Python 3.10+, .NET SDK 8.0+
- 핵심: **언리얼 에디터 미실행 상태에서도 작동**. Monolith / UnrealClaude 미응답 시 즉시 폴백.

**도구 8종:**

| 도구 | 용도 |
|---|---|
| `sb2_asset_meta` | 에셋 메타정보 |
| `sb2_asset_export_list` | ExportMap |
| `sb2_asset_dependencies` | 직접 의존 (hard/soft/both) |
| `sb2_asset_referencers` | 역방향 참조자 (limit 200) |
| `sb2_datatable_rows` | DataTable row 조회 (cursor/filter) |
| `sb2_asset_properties` | UPROPERTY tree (include_defaults 옵션) |
| `sb2_schema_info` | 스키마 정보 |
| `sb2_search_by_class` | 클래스 기반 검색 |

**Monolith 한계 해소 잠재력:**
- Chooser ResultsStructs protected → `sb2_asset_properties` 로 binary level 접근 가능 가능성
- `find_references` false negative (PSD 미등록 판정) → `sb2_asset_referencers` 가 .uasset 직접 스캔이라 더 정확할 가능성 (메모리 [[reference-monolith-animgraph-editing-limits]] 의 5/11 학습)

## ② CodeIndexClient MCP — SB2/UE5 거대 인덱스

- 페이지: https://shiftupcorp.atlassian.net/wiki/spaces/SB2/pages/1236566026/CodeIndexClient+MCP (2025-12-05)
- 외부 서버: `http://10.20.50.205:8000`
- 설치: `SB2프로젝트경로/Program/Tools/MCP/CodeIndexClient/client_mcp.py` + `setup.bat` 가 IP 자동 입력

**인덱스 규모:**
| 프로젝트 | 파일 | 심볼 | 참조 |
|---|---:|---:|---:|
| SB2 | 2,157 | 61,421 | 121,144 |
| UE5 | 229,959 | **3,566,443** | 9,861,441 |

**도구 15종** (find_symbol / search_symbol / search_code(자연어) / get_class_hierarchy / get_class_members / get_module_api / find_references / analyze_includes / detect_include_cycles / get_callers / get_callees / get_call_graph / get_code_metrics / find_similar_code / index_status).

**`cache/ue57/` 와 분담:**
- cache: 13 헤더, 오프라인 즉답 (1ms)
- CodeIndexClient: UE5 전체 229,959 파일, 라이브 인덱스, callers/callees 자동
- 사용 패턴: 캐시에 없거나 caller 추적 필요 → CodeIndexClient 우선

## ③ BlueprintIndexer MCP — Widget BP + C++↔BP 호출

- 페이지: https://shiftupcorp.atlassian.net/wiki/spaces/SB2/pages/1330839553/BlueprintIndexer+MCP (2026-01-05)
- 외부 서버: `10.20.50.205:8300` + 30분 주기 증분 인덱싱
- 설치: `../Tools/MCP/BlueprintIndexer/.venv/Scripts/python.exe`

**도구 8종** (index_blueprints / search_bp_nodes / get_bp_node_info / get_bp_call_graph / **find_cpp_to_bp_calls** / **trace_ui_flow** / get_blueprint_nodes / bp_indexer_status).

**Monolith 한계 해소 잠재력:**
- `blueprint_query.get_graph_data` 가 한 자산 ABP 안 그래프만 조회 → BlueprintIndexer 는 **전 위젯 BP 통합 인덱스 + UE 미응답 시에도 작동** (UAssetAPI C# 파서)
- Widget BP 작업 (SBUserWidget 등) 에 직결. PC_01 ABP 영역은 적용 제한적이지만 SB2 UI 작업 시 압도적.

## 추적 패턴 (SB2 Confluence)

향후 신규 사내 MCP / 빌드 노트 변화 감지:
```
mcp__claude_ai_Atlassian__searchConfluenceUsingCql(
  cloudId="shiftupcorp.atlassian.net",
  cql='space = "SB2" AND (title ~ "MCP" OR title ~ "Monolith" OR title ~ "Build")'
       ' AND lastmodified > now("-7d")',
  limit=20
)
```
- SB2 space key = `SB2`, id = `250282003`
- MCP 폴더 id = `1237549058`
- 주요 contributors: 박용태(PM팀), 최재익(SB2AssetParser/Monolith), 장진영(BlueprintIndexer)

## How to apply

- 다음 흡수 후보 = 사내 MCP 3개 등록 검증. 사용자 환경에 설치된 경우 `.mcp.json` 추가.
- Monolith 한계 발생 시 즉시 3개 중 적합한 폴백 시도:
  - protected/소스레벨 접근 = SB2AssetParser
  - 함수/심볼 cross-ref = CodeIndexClient
  - Widget BP / UI 이벤트 흐름 = BlueprintIndexer
- 새 MCP 페이지 등장 = 주 1회 추적 패턴 실행 (위 CQL)
- 페이지 일부는 confidential — 페이지 본문 직접 인용 금지, 도구 이름/시그니처만 참조.

관련 메모리: [[reference-monolith-animgraph-editing-limits]], [[reference-ue57-source-cache]], [[absorption-candidates-2026-05-18]], [[reference-runreal-python-bypass]].
