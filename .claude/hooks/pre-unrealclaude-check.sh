#!/bin/bash
# PreToolUse Hook: UnrealClaude Bridge 연결 사전 점검
# UnrealClaude MCP 도구 호출 전 서버 상태를 확인

HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 2 http://localhost:3000 2>/dev/null)

if [ "$HTTP_CODE" = "000" ]; then
  cat <<ENDJSON
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"UnrealClaude Bridge 미응답. Node 프로세스 확인: tasklist | grep node. /recover 로 복구 가능."}}
ENDJSON
  exit 0
fi

# 서버 응답 — 통과
exit 0
