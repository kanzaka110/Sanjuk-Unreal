#!/bin/bash
# PostToolUse Hook: Monolith MCP 도구 실행 후 결과 검증
# 도구 실행 결과에서 에러 패턴을 감지하여 자동으로 경고

# stdin에서 도구 결과를 읽음
RESULT=$(cat)

# 에러 패턴 감지
if echo "$RESULT" | grep -qi "error\|failed\|not found\|invalid\|exception"; then
  # 에러 감지 시 경고 출력 (deny하지 않고 정보만 제공)
  cat <<ENDJSON
{"hookSpecificOutput":{"hookEventName":"PostToolUse","notification":"Monolith 액션 결과에 오류 패턴 감지. 에셋 경로 및 파라미터를 확인하세요."}}
ENDJSON
  exit 0
fi

# 정상 — 통과
exit 0
