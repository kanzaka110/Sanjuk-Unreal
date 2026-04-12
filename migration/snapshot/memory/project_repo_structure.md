---
name: 레포 구조
description: Sanjuk-Unreal은 문서 전용 레포 — Tutorial 5개, Briefing 아카이브, 리서치 문서, UE5 바이너리 미포함
type: project
---

Sanjuk-Unreal GitHub 레포는 문서/리서치 전용 (2026-04-09 최신화).

**Why:** UE5 바이너리(4.6GB)를 포함하면 GitHub push 실패. 문서와 UE 프로젝트를 분리.

**How to apply:**
```
Sanjuk-Unreal/
├── Tutorial/
│   ├── Monolith-MCP-Tutorial/     (10편)
│   ├── runreal-MCP-Tutorial/      (12편)
│   ├── AnimNext-Migration-Guide/  (13편)
│   ├── UAF-Setup-Guide/          (12편)
│   └── Chaos-Cloth-Guide/        (10편, 초보자→AAA 천 시뮬레이션)
├── Briefing/                      (날짜별 데일리 브리핑 아카이브)
│   └── 2026-04-06/
├── CLAUDE.md
├── README.md
├── Monolith-Local-Setup-Guide.md
├── UE-Animation-Tech-Report-2026.md
├── UE5-AI-GitHub-Research-2026.md
├── Unreal_Briefing.md
├── .mcp.json
└── .gitignore
```
- .gitignore: MonolithTest/, Plugins/, .mcp.json, .claude/ 등 제외
- UnrealClaude 소스 빌드는 C:/dev/UnrealClaude/에 별도 보관
- 새 문서/튜토리얼은 이 레포에, UE 에셋 작업은 별도 경로에서
