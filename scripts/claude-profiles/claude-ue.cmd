@echo off
rem ue profile: UE/SB2 work - core tools + monolith/unreal-mcp/unrealclaude-bridge, MCP output cap 15k
set "REPO=%~dp0..\.."
claude --settings "%REPO%\.claude\profiles\ue.settings.json" --strict-mcp-config --mcp-config "%REPO%\.claude\profiles\mcp-ue.json" %*
