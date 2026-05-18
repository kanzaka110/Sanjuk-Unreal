#!/bin/bash
# PostToolUse Hook: Monolith MCP 도구 실행 후 결과 검증 + 자동화
#
# 2026-05-18 자동화 강화:
#   A) 에러 패턴 알림 (이전 정밀화 유지)
#   B) mutate 액션 감지 시 백그라운드 자동 백업 (Tuner 잊음 방지)
#   C) monolith_discover/status 호출 후 카탈로그 자동 갱신
#
# stdin JSON 구조 (Claude Code 표준):
#   { "tool_name": "mcp__monolith__<domain>_query", "tool_input": {...}, "tool_response": {...} }
# JSON 파싱은 grep + sed 로. jq 의존 회피.

RESULT=$(cat)
[ -z "$RESULT" ] && exit 0

REPO_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel 2>/dev/null || echo /c/Dev/Sanjuk-Unreal)"
LOG_FILE="$REPO_ROOT/.claude/state/hook.log"
mkdir -p "$(dirname "$LOG_FILE")"

# ── A) 에러 패턴 알림 (기존 정밀화) ─────────────────────────────────────
EMIT_NOTIFY=0
REASON=""

if echo "$RESULT" | grep -qE '"error"[[:space:]]*:[[:space:]]*\{[^}]*"code"[[:space:]]*:[[:space:]]*-32'; then
  EMIT_NOTIFY=1
  REASON="MCP 표준 에러 (-32xxx). 액션명/도메인/파라미터 확인."
fi
if echo "$RESULT" | grep -qE '"isError"[[:space:]]*:[[:space:]]*true'; then
  EMIT_NOTIFY=1
  REASON="${REASON:+$REASON / }Monolith isError=true. 응답 content.text 의 첫 줄 확인."
fi
if echo "$RESULT" | grep -qE 'Failed to save asset|Could not save asset'; then
  EMIT_NOTIFY=1
  REASON="${REASON:+$REASON / }save_asset 실패 (P4 잠금 가능성). 에디터에서 Ctrl+S 또는 P4 Check Out 확인."
fi
if echo "$RESULT" | grep -qE '"compile_status"[[:space:]]*:[[:space:]]*"Failed"|"errors"[[:space:]]*:[[:space:]]*[1-9]'; then
  EMIT_NOTIFY=1
  REASON="${REASON:+$REASON / }Blueprint 컴파일 실패. validate_blueprint 로 상세 확인."
fi

# ── B) mutate 액션 감지 → 자동 백업 (background, fire-and-forget) ──────
# mutate 패턴: action 키 값이 set_*/add_*/remove_*/connect_*/disconnect_*/save_asset/batch_execute
MUTATE_ACTION=""
if MA=$(echo "$RESULT" | grep -oE '"action"[[:space:]]*:[[:space:]]*"(set_[a-z_]+|add_[a-z_]+|remove_[a-z_]+|connect_[a-z_]+|disconnect_[a-z_]+|save_asset|batch_execute|compile_blueprint)"' | head -1); then
  MUTATE_ACTION=$(echo "$MA" | sed -E 's/.*"action"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/')
fi

# asset_path 추출 (tool_input 안 또는 params 안)
ASSET_PATH=""
if AP=$(echo "$RESULT" | grep -oE '"asset_path"[[:space:]]*:[[:space:]]*"/Game/[^"]+"' | head -1); then
  ASSET_PATH=$(echo "$AP" | sed -E 's/.*"asset_path"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/')
fi

if [ -n "$MUTATE_ACTION" ] && [ -n "$ASSET_PATH" ] && [ "$MUTATE_ACTION" != "save_asset" ] && [ "$MUTATE_ACTION" != "compile_blueprint" ]; then
  # save/compile 자체는 백업 트리거에서 제외 (이미 변경 끝난 직후라 의미 X)
  STAMP=$(date +%Y%m%d_%H%M%S)
  LABEL="auto_${MUTATE_ACTION}"
  echo "[$STAMP] auto-backup trigger: $MUTATE_ACTION on $ASSET_PATH" >> "$LOG_FILE"
  # background fire-and-forget. py 가 PATH 에 있어야 함. py 실패해도 hook 통과.
  (cd "$REPO_ROOT" && py scripts/abp_backup.py backup "$ASSET_PATH" "$LABEL" >> "$LOG_FILE" 2>&1) &
fi

# ── C) monolith_discover / monolith_status 호출 시 카탈로그 자동 갱신 ──
if echo "$RESULT" | grep -qE '"(total_actions|namespaces)"[[:space:]]*:'; then
  STAMP=$(date +%Y%m%d_%H%M%S)
  echo "[$STAMP] auto-catalog-refresh: total_actions detected" >> "$LOG_FILE"
  (cd "$REPO_ROOT" && py scripts/save_discover_snapshot.py >> "$LOG_FILE" 2>&1) &
fi

# ── 결과 출력 ──────────────────────────────────────────────────────────
if [ "$EMIT_NOTIFY" -eq 1 ]; then
  cat <<ENDJSON
{"hookSpecificOutput":{"hookEventName":"PostToolUse","notification":"$REASON"}}
ENDJSON
fi

exit 0
