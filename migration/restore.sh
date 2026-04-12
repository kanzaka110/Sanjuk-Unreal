#!/bin/bash
# =============================================================================
# restore.sh — 새 PC에서 Claude Code + UE5 환경 복원
# env.local 파일에서 경로를 읽어 자동으로 복원.
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SNAPSHOT_DIR="$SCRIPT_DIR/snapshot"
ENV_FILE="$SCRIPT_DIR/env.local"

# --- env.local 로드 ---
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ env.local 파일이 없습니다."
    echo "   cp migration/env.example migration/env.local"
    echo "   편집 후 다시 실행하세요."
    exit 1
fi

source "$ENV_FILE"

# 필수 변수 검증
for var in USER_HOME REPO_ROOT_PATH UE_PROJECT_ROOT; do
    if [ -z "${!var:-}" ]; then
        echo "❌ env.local에 $var 가 설정되지 않았습니다."
        exit 1
    fi
done

echo "=== Claude Code 환경 복원 ==="
echo "USER_HOME:       $USER_HOME"
echo "REPO_ROOT_PATH:  $REPO_ROOT_PATH"
echo "UE_PROJECT_ROOT: $UE_PROJECT_ROOT"
echo ""

# --- 1. 글로벌 룰 복원 ---
echo "[1/5] 글로벌 룰 복원..."
GLOBAL_RULES_DST="$USER_HOME/.claude/rules/common"
mkdir -p "$GLOBAL_RULES_DST"
if [ -d "$SNAPSHOT_DIR/global-rules" ] && [ "$(ls -A "$SNAPSHOT_DIR/global-rules")" ]; then
    cp "$SNAPSHOT_DIR/global-rules/"*.md "$GLOBAL_RULES_DST/"
    echo "  → $(ls "$GLOBAL_RULES_DST/"*.md | wc -l)개 파일 복원됨"
else
    echo "  ⚠️ 스냅샷에 글로벌 룰 없음"
fi

# --- 2. 메모리 복원 ---
echo "[2/5] 메모리 복원..."
# Claude Code 프로젝트 키 생성 (경로 기반)
# Windows: C:\dev\Sanjuk-Unreal → C--dev-Sanjuk-Unreal
# Linux: /home/user/Sanjuk-Unreal → -home-user-Sanjuk-Unreal
if [ -n "${CLAUDE_PROJECT_KEY:-}" ]; then
    PROJECT_KEY="$CLAUDE_PROJECT_KEY"
else
    # 자동 추정: 경로에서 키 생성
    PROJECT_KEY=$(echo "$REPO_ROOT_PATH" | sed 's|[:/\\]|-|g' | sed 's|^-*||')
    echo "  ℹ️ 자동 추정 프로젝트 키: $PROJECT_KEY"
    echo "  (정확하지 않으면 env.local에 CLAUDE_PROJECT_KEY를 수동 설정하세요)"
fi

MEMORY_DST="$USER_HOME/.claude/projects/$PROJECT_KEY/memory"
mkdir -p "$MEMORY_DST"
if [ -d "$SNAPSHOT_DIR/memory" ] && [ "$(ls -A "$SNAPSHOT_DIR/memory")" ]; then
    cp "$SNAPSHOT_DIR/memory/"*.md "$MEMORY_DST/"
    echo "  → $(ls "$MEMORY_DST/"*.md | wc -l)개 파일 복원됨"
    echo "  → 경로: $MEMORY_DST"
else
    echo "  ⚠️ 스냅샷에 메모리 없음"
fi

# --- 3. settings.local.json 복원 ---
echo "[3/5] settings.local.json 복원..."
SETTINGS_TPL="$SNAPSHOT_DIR/settings.local.json.tpl"
SETTINGS_DST="$REPO_ROOT/.claude/settings.local.json"
if [ -f "$SETTINGS_TPL" ]; then
    # UNC 경로 생성: /c/Users/user → //c/Users/user
    USER_HOME_UNC="/$(echo "$USER_HOME" | sed 's|^/||')"
    sed \
        -e "s|{{REPO_ROOT}}|$REPO_ROOT_PATH|g" \
        -e "s|{{USER_HOME}}|$USER_HOME|g" \
        -e "s|{{USER_HOME_UNC}}|$USER_HOME_UNC|g" \
        -e "s|{{UE_PROJECT_ROOT}}|$UE_PROJECT_ROOT|g" \
        "$SETTINGS_TPL" > "$SETTINGS_DST"
    echo "  → 복원 완료"
else
    echo "  ⚠️ 템플릿 없음"
fi

# --- 4. .mcp.json 복원 ---
echo "[4/5] .mcp.json 복원..."
MCP_TPL="$SNAPSHOT_DIR/mcp.json.tpl"
MCP_DST="$REPO_ROOT/.mcp.json"
if [ -f "$MCP_TPL" ]; then
    sed \
        -e "s|{{UE_PROJECT_ROOT}}|$UE_PROJECT_ROOT|g" \
        "$MCP_TPL" > "$MCP_DST"
    echo "  → 복원 완료"
    echo "  ⚠️ .mcp.json이 덮어씌워졌습니다. git diff로 확인하세요."
else
    echo "  ⚠️ 템플릿 없음"
fi

# --- 5. 검증 ---
echo "[5/5] 환경 검증..."
echo ""
echo "┌─────────────────────────────────────────────┐"
echo "│ 자동 복원 결과                               │"
echo "├─────────────────────┬───────────────────────┤"

check_exists() {
    if [ -e "$1" ]; then echo "✅"; else echo "❌"; fi
}

printf "│ %-20s│ %-22s│\n" "글로벌 룰" "$(check_exists "$GLOBAL_RULES_DST/agents.md")"
printf "│ %-20s│ %-22s│\n" "메모리" "$(check_exists "$MEMORY_DST/MEMORY.md")"
printf "│ %-20s│ %-22s│\n" "settings.local.json" "$(check_exists "$SETTINGS_DST")"
printf "│ %-20s│ %-22s│\n" ".mcp.json" "$(check_exists "$MCP_DST")"
echo "└─────────────────────┴───────────────────────┘"
echo ""
echo "=== 수동 확인 필요 ==="
echo "1. Claude Code 로그인: claude 실행 후 인증"
echo "2. UE5 에디터 실행 후 Monolith/UnrealClaude 플러그인 확인"
echo "3. claude 에서 /doctor 실행하여 전체 환경 점검"
echo "4. 프로젝트 키가 맞는지 확인: claude 실행 후 메모리 인식 여부 확인"
echo "   (인식 안 되면 CLAUDE_PROJECT_KEY를 env.local에 수정)"
