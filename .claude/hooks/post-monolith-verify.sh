#!/bin/bash
# PostToolUse Hook: Monolith MCP 도구 실행 후 결과 검증
#
# 이전 버전은 `grep -qi "error|failed|not found|invalid|exception"` 로 너무 광범위 매치
# → disconnect_pins 응답의 "removed" 같은 정상 단어도 false positive. 정상 응답에
# 등장하는 "error_count":0 같은 카운터 키도 잡아냄.
#
# 정밀화 (2026-05-18):
#   1) MCP 표준 에러 응답: 최상위 "error" 객체 (코드 + 메시지)
#   2) Monolith 내부 에러:  result.isError == true
#   3) tools/call 한도 초과: "code":-32xxx 패턴
#   4) save_asset P4 잠금:  "Failed to save asset" / "Could not save"
#   5) 컴파일 실패:         "isError":true 옆에 "compile" 등장
# 그 외 응답 본문의 일반 단어("error", "failed")는 무시.

RESULT=$(cat)

# 빈 입력은 통과
if [ -z "$RESULT" ]; then
  exit 0
fi

EMIT_NOTIFY=0
REASON=""

# 1) 최상위 MCP error 객체 (JSON-RPC 표준 -32xxx)
if echo "$RESULT" | grep -qE '"error"[[:space:]]*:[[:space:]]*\{[^}]*"code"[[:space:]]*:[[:space:]]*-32'; then
  EMIT_NOTIFY=1
  REASON="MCP 표준 에러 (-32xxx). 액션명/도메인/파라미터 확인."
fi

# 2) Monolith 내부 isError true
if echo "$RESULT" | grep -qE '"isError"[[:space:]]*:[[:space:]]*true'; then
  EMIT_NOTIFY=1
  REASON="${REASON:+$REASON / }Monolith isError=true. 응답 content.text 의 첫 줄 확인."
fi

# 3) save_asset P4 잠금
if echo "$RESULT" | grep -qE 'Failed to save asset|Could not save asset'; then
  EMIT_NOTIFY=1
  REASON="${REASON:+$REASON / }save_asset 실패 (P4 잠금 가능성). 에디터에서 Ctrl+S 또는 P4 Check Out 확인."
fi

# 4) blueprint compile 실패 ("compile_status": "Failed" 또는 errors > 0 + ...)
if echo "$RESULT" | grep -qE '"compile_status"[[:space:]]*:[[:space:]]*"Failed"|"errors"[[:space:]]*:[[:space:]]*[1-9]'; then
  EMIT_NOTIFY=1
  REASON="${REASON:+$REASON / }Blueprint 컴파일 실패. validate_blueprint 로 상세 확인."
fi

if [ "$EMIT_NOTIFY" -eq 1 ]; then
  # JSON 출력 시 따옴표는 외부 single quote 로 escape
  cat <<ENDJSON
{"hookSpecificOutput":{"hookEventName":"PostToolUse","notification":"$REASON"}}
ENDJSON
  exit 0
fi

# 정상 — 통과
exit 0
