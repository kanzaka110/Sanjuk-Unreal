#!/bin/bash
# =============================================================================
# backup.sh — Claude Code + UE5 환경 백업
# 현재 PC에서 실행. git 미추적 파일을 migration/snapshot/에 저장.
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SNAPSHOT_DIR="$SCRIPT_DIR/snapshot"

# 현재 사용자 홈 (Windows Git Bash: /c/Users/ohmil)
USER_HOME="$HOME"
# Windows 스타일 경로 변환
USER_HOME_WIN=$(echo "$USER_HOME" | sed 's|^/\([a-z]\)/|/\1/|')

echo "=== Claude Code 환경 백업 ==="
echo "REPO_ROOT: $REPO_ROOT"
echo "USER_HOME: $USER_HOME"
echo ""

# --- 1. 글로벌 룰 백업 ---
echo "[1/4] 글로벌 룰 백업..."
GLOBAL_RULES="$USER_HOME/.claude/rules/common"
if [ -d "$GLOBAL_RULES" ]; then
    cp -r "$GLOBAL_RULES/"*.md "$SNAPSHOT_DIR/global-rules/" 2>/dev/null || true
    echo "  → $(ls "$SNAPSHOT_DIR/global-rules/" | wc -l)개 파일 복사됨"
else
    echo "  ⚠️ 글로벌 룰 없음: $GLOBAL_RULES"
fi

# --- 2. 메모리 백업 ---
echo "[2/4] 메모리 백업..."
# Claude Code 프로젝트 키 자동 감지
MEMORY_DIR=""
for dir in "$USER_HOME/.claude/projects/"*Sanjuk-Unreal*/memory; do
    if [ -d "$dir" ]; then
        MEMORY_DIR="$dir"
        break
    fi
done

if [ -n "$MEMORY_DIR" ] && [ -d "$MEMORY_DIR" ]; then
    cp "$MEMORY_DIR/"*.md "$SNAPSHOT_DIR/memory/" 2>/dev/null || true
    echo "  → $(ls "$SNAPSHOT_DIR/memory/" | wc -l)개 파일 복사됨"
    echo "  → 소스: $MEMORY_DIR"
else
    echo "  ⚠️ 메모리 디렉토리 미발견"
fi

# --- 3. settings.local.json 템플릿화 ---
echo "[3/4] settings.local.json 템플릿 생성..."
SETTINGS_SRC="$REPO_ROOT/.claude/settings.local.json"
if [ -f "$SETTINGS_SRC" ]; then
    # 절대 경로를 플레이스홀더로 치환
    sed \
        -e "s|C:/dev/Sanjuk-Unreal|{{REPO_ROOT}}|g" \
        -e "s|C:\\\\dev\\\\Sanjuk-Unreal|{{REPO_ROOT}}|g" \
        -e "s|C:/Users/ohmil|{{USER_HOME}}|g" \
        -e "s|C:\\\\Users\\\\ohmil|{{USER_HOME}}|g" \
        -e "s|//c/Users/ohmil|{{USER_HOME_UNC}}|g" \
        -e "s|C:/Users/ohmil/OneDrive/문서/Unreal Projects/MonolithTest|{{UE_PROJECT_ROOT}}|g" \
        "$SETTINGS_SRC" > "$SNAPSHOT_DIR/settings.local.json.tpl"
    echo "  → 템플릿 생성 완료"
else
    echo "  ⚠️ settings.local.json 없음"
fi

# --- 4. .mcp.json 템플릿화 ---
echo "[4/4] .mcp.json 템플릿 생성..."
MCP_SRC="$REPO_ROOT/.mcp.json"
if [ -f "$MCP_SRC" ]; then
    sed \
        -e "s|C:/Users/ohmil/OneDrive/문서/Unreal Projects/MonolithTest|{{UE_PROJECT_ROOT}}|g" \
        -e "s|C:\\\\Users\\\\ohmil\\\\OneDrive\\\\문서\\\\Unreal Projects\\\\MonolithTest|{{UE_PROJECT_ROOT}}|g" \
        "$MCP_SRC" > "$SNAPSHOT_DIR/mcp.json.tpl"
    echo "  → 템플릿 생성 완료"
else
    echo "  ⚠️ .mcp.json 없음"
fi

echo ""
echo "=== 백업 완료 ==="
echo "파일 목록:"
find "$SNAPSHOT_DIR" -type f | sort
echo ""
echo "다음 단계: git add migration/snapshot && git commit && git push"
