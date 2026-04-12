---
name: MCP 구성 현황
description: Monolith(9316) + UnrealClaude(3000) + runreal(stdio) 3개 MCP 서버 병행, Monolith 최우선
type: project
---

`.mcp.json`에 MCP 서버 3개 등록 (2026-04-06 최신화).

**Why:** Monolith(에디터 제어 깊이) + UnrealClaude(API 문서 컨텍스트/코딩) + runreal(Python 확장) 병행으로 최대 커버리지.

**How to apply:**
- **Monolith v0.12.0** — `http://localhost:9316/mcp` (HTTP 모드). 1,125 액션, 16 모듈. 에디터 제어 최우선.
- **UnrealClaude v1.4.1** — `unrealclaude-bridge` (node stdio → http://localhost:3000). INJECT_CONTEXT=true. API 문서 컨텍스트 11개 카테고리. Monolith 보조.
- **runreal MCP** — `npx -y @runreal/unreal-mcp`. Python 기반 UE5 자동화. UAF 대비용.
- 포트 충돌 없음: Monolith 9316, UnrealClaude 3000
- PC 독립적: HTTP 모드라 경로 무관 (unrealclaude-bridge만 절대경로 사용)
