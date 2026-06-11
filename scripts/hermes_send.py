"""Hermes Slack 채널로 메시지 직송 (Hermes 봇 토큰).

claude.ai Slack 커넥터는 회사 워크스페이스 정책상 비공개 채널 접근 불가 →
Hermes 봇 자신의 토큰(xoxb)으로 chat.postMessage. 봇은 자기가 멤버인 방에
항상 쓸 수 있어 초대/관리자 정책 무관. 셋업은 .env 두 줄이 전부.

사용:
    py scripts/hermes_send.py "보낼 텍스트"
    py scripts/hermes_send.py --file scripts/_hermes_msg.txt

환경변수 (루트 .env):
    SLACK_BOT_TOKEN       — Hermes 봇 토큰 (xoxb-...)
    HERMES_SLACK_CHANNEL  — 대상 채널 ID (C... 또는 봇방 D...)

주의: 메시지가 Hermes 명의로 게시됨. Hermes가 이를 입력으로 처리하려면
Hermes 쪽에서 [LOCAL-CLAUDE] 마커 self-message 분기 필요.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
MARKER = "[LOCAL-CLAUDE]"
MAX_CHUNK = 3800  # Slack 표시 잘림(~4000자) 회피용 분할 기준


def load_env(path: Path) -> None:
    """루트 .env를 읽어 미설정 env만 채운다 (dotenv 의존성 없이)."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        sys.exit(f"[hermes_send] env {name} 미설정 — 루트 .env 에 추가 필요")
    return value


def split_chunks(text: str, limit: int = MAX_CHUNK) -> list[str]:
    """줄 경계 우선으로 limit 이하 청크 분할."""
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    current = ""
    for line in text.splitlines(keepends=True):
        if len(current) + len(line) > limit:
            if current:
                chunks.append(current)
            while len(line) > limit:
                chunks.append(line[:limit])
                line = line[limit:]
            current = line
        else:
            current += line
    if current:
        chunks.append(current)
    return chunks


def post_message(token: str, channel: str, text: str, thread_ts: str | None = None) -> str:
    """메시지 전송 후 ts 반환 (스레드 부모로 재사용 가능)."""
    payload: dict[str, str] = {"channel": channel, "text": text}
    if thread_ts:
        payload["thread_ts"] = thread_ts
    res = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
        timeout=30,
    )
    res.raise_for_status()
    body = res.json()
    if not body.get("ok"):
        sys.exit(f"[hermes_send] Slack API 실패: {body.get('error')}")
    return body.get("ts", "")


def main() -> None:
    parser = argparse.ArgumentParser(description="Hermes Slack 채널로 메시지 전송")
    parser.add_argument("text", nargs="?", help="보낼 텍스트 (또는 --file)")
    parser.add_argument("--file", help="보낼 텍스트 파일 경로 (utf-8)")
    parser.add_argument("--channel", help="HERMES_SLACK_CHANNEL 오버라이드")
    parser.add_argument("--thread-ts", help="이 ts의 스레드에 답글로 전송")
    parser.add_argument("--no-marker", action="store_true", help=f"{MARKER} 접두 마커 생략")
    args = parser.parse_args()

    load_env(ROOT / ".env")
    token = require_env("SLACK_BOT_TOKEN")
    channel = (args.channel or require_env("HERMES_SLACK_CHANNEL")).strip()

    if args.file:
        text = Path(args.file).read_text(encoding="utf-8").strip()
    elif args.text:
        text = args.text.strip()
    else:
        sys.exit("[hermes_send] 보낼 내용 없음 — 텍스트 인자 또는 --file 지정")
    if not text:
        sys.exit("[hermes_send] 빈 메시지는 보내지 않음")

    if not args.no_marker and not text.startswith(MARKER):
        text = f"{MARKER}\n{text}"

    chunks = split_chunks(text)
    for i, chunk in enumerate(chunks, 1):
        post_message(token, channel, chunk, thread_ts=args.thread_ts)
        print(f"[hermes_send] {channel} 전송 {i}/{len(chunks)} ({len(chunk)} chars)")


if __name__ == "__main__":
    main()
