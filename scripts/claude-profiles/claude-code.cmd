@echo off
rem code profile: general implementation - full core tools, no MCP, Sonnet
set "REPO=%~dp0..\.."
claude --settings "%REPO%\.claude\profiles\code.settings.json" --strict-mcp-config --mcp-config "%REPO%\.claude\profiles\mcp-none.json" %*
