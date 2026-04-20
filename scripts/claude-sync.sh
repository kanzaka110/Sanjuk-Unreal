#!/usr/bin/env bash
# Sanjuk-Unreal 메모리 GCP VM 동기화 스크립트
# 사용법:
#   ./scripts/claude-sync.sh upload   # 로컬 → GCP
#   ./scripts/claude-sync.sh download # GCP → 로컬
#   ./scripts/claude-sync.sh status   # 동기화 상태 확인

set -euo pipefail

GCP_PROJECT="sanjuk-talk-bot"
GCP_ZONE="us-central1-b"
GCP_INSTANCE="sanjuk-project"
REMOTE_DIR="/home/ohmil/claude-sync"
REMOTE_MEMORY="$REMOTE_DIR/memory-unreal"

if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    CLAUDE_HOME="$(cygpath -u "$USERPROFILE")/.claude"
else
    CLAUDE_HOME="$HOME/.claude"
fi

MEMORY_DIR="$CLAUDE_HOME/projects/C--Dev-Sanjuk-Unreal/memory"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"; }

gcp_ssh() {
    gcloud compute ssh "$GCP_INSTANCE" \
        --project="$GCP_PROJECT" \
        --zone="$GCP_ZONE" \
        --command="$1"
}

gcp_scp() {
    gcloud compute scp "$1" "$GCP_INSTANCE:$2" \
        --project="$GCP_PROJECT" \
        --zone="$GCP_ZONE"
}

gcp_scp_from() {
    gcloud compute scp "$GCP_INSTANCE:$1" "$2" \
        --project="$GCP_PROJECT" \
        --zone="$GCP_ZONE"
}

upload() {
    log "=== 업로드 시작: 로컬 → GCP (memory-unreal) ==="

    if [ ! -d "$MEMORY_DIR" ]; then
        log "메모리 디렉토리 없음: $MEMORY_DIR"
        exit 1
    fi

    local tarball="/tmp/mem-unreal-upload-$$.tgz"
    log "tarball 생성 중..."
    (cd "$MEMORY_DIR" && tar czf "$tarball" .)

    log "GCP에 tarball 전송..."
    gcp_scp "$tarball" "/tmp/mem-unreal-upload.tgz" >/dev/null 2>&1

    local ts
    ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)

    log "원격 단일 스크립트 실행..."
    gcp_ssh "bash -c '
        sudo chown -R \$USER:\$USER $REMOTE_MEMORY 2>/dev/null || true
        rm -rf $REMOTE_MEMORY
        mkdir -p $REMOTE_MEMORY
        tar xzf /tmp/mem-unreal-upload.tgz -C $REMOTE_MEMORY
        rm -f /tmp/mem-unreal-upload.tgz
        echo \"$ts upload-unreal from $(hostname)\" >> $REMOTE_DIR/meta/sync-log.txt
    '" >/dev/null 2>&1

    local count
    count=$(ls "$MEMORY_DIR" | wc -l)
    log "메모리 ${count}개 파일 완료"

    rm -f "$tarball"
    log "=== 업로드 완료 ==="
}

download() {
    log "=== 다운로드 시작: GCP → 로컬 (memory-unreal) ==="

    if ! gcp_ssh "test -d $REMOTE_MEMORY && test -n \"\$(ls $REMOTE_MEMORY 2>/dev/null)\"" >/dev/null 2>&1; then
        log "GCP에 동기화 데이터 없음. 먼저 upload를 실행하세요."
        exit 1
    fi

    log "GCP에서 tarball 생성..."
    gcp_ssh "bash -c 'cd $REMOTE_MEMORY && tar czf /tmp/mem-unreal-download.tgz .'" >/dev/null 2>&1

    local tarball="/tmp/mem-unreal-download-$$.tgz"
    log "로컬로 전송..."
    gcp_scp_from "/tmp/mem-unreal-download.tgz" "$tarball" >/dev/null 2>&1

    mkdir -p "$MEMORY_DIR"
    log "로컬 추출 중..."
    (cd "$MEMORY_DIR" && tar xzf "$tarball")

    gcp_ssh "rm -f /tmp/mem-unreal-download.tgz" >/dev/null 2>&1
    rm -f "$tarball"
    log "=== 다운로드 완료 ==="
}

status() {
    log "=== 동기화 상태 ==="
    echo ""
    echo "로컬 메모리: $(ls "$MEMORY_DIR" 2>/dev/null | wc -l)개 파일 ($MEMORY_DIR)"
    echo ""
    echo "--- GCP 마지막 동기화 로그 ---"
    gcp_ssh "tail -5 $REMOTE_DIR/meta/sync-log.txt 2>/dev/null || echo '동기화 이력 없음'"
    echo ""
    echo "--- GCP 저장 현황 ---"
    gcp_ssh "echo memory-unreal: \$(ls $REMOTE_MEMORY/ 2>/dev/null | wc -l)개"
}

case "${1:-help}" in
    upload)   upload ;;
    download) download ;;
    status)   status ;;
    *)
        echo "사용법: $0 {upload|download|status}"
        echo ""
        echo "  upload   - 로컬 메모리 → GCP VM 업로드"
        echo "  download - GCP VM → 로컬 메모리 다운로드"
        echo "  status   - 동기화 상태 확인"
        exit 1
        ;;
esac
