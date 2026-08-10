@echo off
rem read profile: lookup only - Read/Grep/Glob, no MCP, Haiku
set "REPO=%~dp0..\.."
claude --settings "%REPO%\.claude\profiles\read.settings.json" --strict-mcp-config --mcp-config "%REPO%\.claude\profiles\mcp-none.json" %*
