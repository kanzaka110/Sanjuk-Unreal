---
name: sb2-internal-mcp-pending
description: SB2 사내 MCP 3개 등록 작업 — P4 sync + 사내 서버 가동 대기 중. 2026-05-18 진단 결과 두 가지 모두 미충족.
metadata: 
  node_type: memory
  type: project
  originSessionId: ea3be7a5-d8f0-4249-af75-76ddb6a92c3d
---

SB2 사내 MCP 3개 (SB2AssetParser / CodeIndexClient / BlueprintIndexer) 등록 진행 중. **2026-05-18 진단 결과 두 가지 차단 요인** → 사용자 작업 대기.

**Why:** [[reference-sb2-internal-mcps]] 에서 발견한 사내 MCP 등록 시도 중 다음 확인:
1. **P4 sync 누락** — `//depot/main/Program/Tools/MCP/` 폴더가 로컬 워크스페이스에 없음. `E:/Perforce/SB2/Workspace/Tools/` 에는 GameDesign 만 sync. `D:/Perforce/SB2/UE5_Release_5.7/Client/` 는 엔진 소스만.
2. **사내 서버 미가동** — `ping 10.20.50.205` = 0ms (사내망 OK) 인데 `8000` (CodeIndexClient) / `8300` (BlueprintIndexer) 둘 다 HTTP 000 (timeout). 서버 프로세스 꺼졌거나 방화벽 차단.

**How to apply:**
- 다음 세션에서 사용자가 P4 sync 끝났다고 통보 시 즉시 등록 절차 재개.
- 사용자 작업 (사용자가 직접 수행):
  1. P4 클라이언트 → `//depot/main/Program/Tools/MCP/...` sync (적어도 SB2AssetParser, BlueprintIndexer, CodeIndexClient 세 폴더)
  2. SB2AssetParser/Setup-SB2AssetParser.bat 실행 (Python 3.10+, .NET SDK 8.0+ 필요)
  3. PM팀에 사내 서버 (10.20.50.205:8000, 10.20.50.205:8300) 가동 상태 문의
- 재개 시 (claude 측):
  1. `Glob` 으로 sync 된 경로 검증
  2. `.mcp.json` 에 stdio (SB2AssetParser, BlueprintIndexer) + python+env (CodeIndexClient) 추가
  3. `/doctor` 로 새 MCP 응답 확인
  4. PoC: SB2AssetParser 로 PC_01 ChooserTable `sb2_asset_properties` 시도 → [[reference-monolith-animgraph-editing-limits]] 의 Chooser ResultsStructs protected 우회 검증

**.mcp.json 등록 명세 (참고 — 실제 등록은 sync 후):**
- SB2AssetParser: stdio, `../Tools/MCP/SB2AssetParser/tools/uv.exe --directory ../Tools/MCP/SB2AssetParser/Mcp run sb2_asset_mcp.py`
- BlueprintIndexer: stdio, `../Tools/MCP/BlueprintIndexer/.venv/Scripts/python.exe ../Tools/MCP/BlueprintIndexer/client/bp_indexer_mcp.py`
- CodeIndexClient: stdio, `python <SB2경로>/Program/Tools/MCP/CodeIndexClient/client_mcp.py` + env `CODE_INDEX_SERVER_URL=http://10.20.50.205:8000`

관련 메모리: [[reference-sb2-internal-mcps]], [[reference-monolith-animgraph-editing-limits]], [[project-sb2-monolith-pending]].
