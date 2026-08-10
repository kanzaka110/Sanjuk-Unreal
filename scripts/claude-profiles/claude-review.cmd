@echo off
rem review profile: read-only review - Edit/Write denied, no MCP, Opus + always thinking
set "REPO=%~dp0..\.."
claude --settings "%REPO%\.claude\profiles\review.settings.json" --strict-mcp-config --mcp-config "%REPO%\.claude\profiles\mcp-none.json" %*
