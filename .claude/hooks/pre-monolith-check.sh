#!/bin/bash
# PreToolUse Hook: Monolith MCP 서버 연결 사전 점검
# Monolith MCP 도구 호출 전 서버 상태를 확인하여 불필요한 실패를 방지

HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 2 http://localhost:9316/mcp 2>/dev/null)

if [ "$HTTP_CODE" != "200" ] && [ "$HTTP_CODE" != "405" ]; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: "Monolith MCP 서버 미응답 (HTTP '"$HTTP_CODE"'). UE5 에디터가 실행 중인지 확인하세요. /recover 로 복구 가능."
    }
  }'
  exit 0
fi

# 서버 정상 — 통과
exit 0
