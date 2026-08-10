@echo off
rem full profile: legacy behavior - all 6 MCP servers (monolith/unreal-mcp/unrealclaude-bridge/context7/maya/confluence)
set "REPO=%~dp0..\.."
claude --strict-mcp-config --mcp-config "%REPO%\.mcp.json" %*
