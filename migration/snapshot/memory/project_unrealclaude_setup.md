---
name: UnrealClaude 설치 현황
description: UnrealClaude v1.4.1 — MonolithTest에 설치, MCP 브릿지(port 3000), API 문서 컨텍스트 11개, Monolith 보조 역할
type: project
---

UnrealClaude v1.4.1이 MonolithTest 프로젝트에 설치됨 (2026-04-06).

**Why:** Monolith(에디터 제어 깊이)의 보조 도구로, API 문서 컨텍스트 자동 주입과 C++ 코딩 어시스턴트 역할.

**How to apply:**
- 플러그인 경로: `MonolithTest/Plugins/UnrealClaude/`
- MCP 브릿지: `.mcp.json`에 `unrealclaude-bridge` 등록 (port 3000, INJECT_CONTEXT=true)
- 에디터 내 채팅: Tools > Claude Assistant
- API 문서 컨텍스트 11개: actor, animation, assets, blueprint, character, enhanced_input, material, parallel_workflows, replication, slate, ue-core-api
- 소스 빌드 위치: `C:/dev/UnrealClaude/` (git clone --recurse-submodules)
- 빌드 방법: RunUAT.bat BuildPlugin (.NET Framework 4.8.1 Developer Pack 필요)
- MonolithTest에 CLAUDE.md 생성됨 (프로젝트 컨텍스트 자동 주입용)
- **우선순위: Monolith > UnrealClaude > runreal** (기능 겹치면 항상 Monolith 우선)
