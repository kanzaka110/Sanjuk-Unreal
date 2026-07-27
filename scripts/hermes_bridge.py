"""Hermes 역방향 검토 브리지 — 질문/검증 요청을 Slack으로 보내고 응답을 회수.

`/hermes 질문:<본문>` → mode=question, `/hermes 검증:<본문>` → mode=verify.
일반 `/hermes [주제]` 다이제스트(hermes_send.py)와 Stop 훅 자동공유는 건드리지 않는다.

동작:
1. 매 요청마다 새 hreq_ task ID 생성
2. [HERMES-REQUEST v1] 포맷의 top-level 메시지를 chat.postMessage로 전송, ts 저장
3. 같은 스레드를 conversations.replies로 3초 간격, 최대 180초 폴링
4. [HERMES-RESPONSE v1] + 원 task ID 정확 일치 응답의 body만 stdout으로 반환
5. timeout/API 오류 시 같은 task ID 재전송 없이 BLOCK/HOLD + 실패 단계만 출력

사용:
    py scripts/hermes_bridge.py --mode question "질문 본문"
    py scripts/hermes_bridge.py --mode verify --file scripts/_hermes_req.txt

환경변수 (루트 .env): SLACK_BOT_TOKEN, HERMES_SLACK_CHANNEL (하드코딩 금지)
보안: 토큰·원시 Slack 응답·전체 transcript 출력/저장 금지.
"""

from __future__ import annotations

import argparse
import sys
import time
import uuid
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hermes_send import load_env, require_env  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
REQUEST_MARKER = "[HERMES-REQUEST v1]"
RESPONSE_MARKER = "[HERMES-RESPONSE v1]"
DOMAIN = "ue-sb2"
VALID_MODES = ("question", "verify")
POLL_INTERVAL_SEC = 3.0
POLL_TIMEOUT_SEC = 180.0
SLACK_API = "https://slack.com/api"


class BridgeError(RuntimeError):
    """Slack API 실패 (오류 코드만 담고 원시 응답은 담지 않는다)."""


def new_task_id() -> str:
    """요청마다 유일한 hreq_ task ID 생성."""
    return f"hreq_{uuid.uuid4().hex[:12]}"


def build_request(task_id: str, mode: str, body: str) -> str:
    """[HERMES-REQUEST v1] top-level 메시지 본문 조립 (포맷 고정)."""
    if mode not in VALID_MODES:
        raise ValueError(f"mode는 {VALID_MODES} 중 하나여야 함: {mode!r}")
    return (
        f"{REQUEST_MARKER}\n"
        f"task_id: {task_id}\n"
        f"mode: {mode}\n"
        f"domain: {DOMAIN}\n"
        f"reply_required: true\n"
        f"body:\n"
        f"{body}"
    )


def post_request(token: str, channel: str, text: str) -> str:
    """top-level 전송 후 스레드 부모 ts 반환."""
    res = requests.post(
        f"{SLACK_API}/chat.postMessage",
        headers={"Authorization": f"Bearer {token}"},
        json={"channel": channel, "text": text},
        timeout=30,
    )
    res.raise_for_status()
    data = res.json()
    if not data.get("ok"):
        raise BridgeError(f"Slack 오류: {data.get('error')}")
    ts = data.get("ts", "")
    if not ts:
        raise BridgeError("응답에 ts 없음")
    return ts


def parse_response(text: str, task_id: str) -> str | None:
    """[HERMES-RESPONSE v1] + task_id 정확 일치면 body 반환, 아니면 None."""
    lines = text.strip().splitlines()
    if not lines or lines[0].strip() != RESPONSE_MARKER:
        return None
    found_task_id: str | None = None
    body_start: int | None = None
    for i, line in enumerate(lines[1:], start=1):
        stripped = line.strip()
        if stripped.startswith("task_id:"):
            found_task_id = stripped[len("task_id:"):].strip()
        elif stripped == "body:":
            body_start = i + 1
            break
    if found_task_id != task_id or body_start is None:
        return None
    return "\n".join(lines[body_start:]).strip()


def fetch_replies(token: str, channel: str, thread_ts: str) -> list[dict]:
    """저장한 부모 ts의 스레드 메시지 목록 조회."""
    res = requests.get(
        f"{SLACK_API}/conversations.replies",
        headers={"Authorization": f"Bearer {token}"},
        params={"channel": channel, "ts": thread_ts, "limit": 100},
        timeout=30,
    )
    res.raise_for_status()
    data = res.json()
    if not data.get("ok"):
        raise BridgeError(f"Slack 오류: {data.get('error')}")
    return data.get("messages", [])


def wait_response(
    token: str,
    channel: str,
    thread_ts: str,
    task_id: str,
    timeout: float = POLL_TIMEOUT_SEC,
    interval: float = POLL_INTERVAL_SEC,
    _sleep=time.sleep,
    _clock=time.monotonic,
) -> str | None:
    """같은 스레드에서 task_id 일치 응답 body를 회수. timeout이면 None."""
    deadline = _clock() + timeout
    while True:
        for msg in fetch_replies(token, channel, thread_ts):
            if msg.get("ts") == thread_ts:
                continue  # 부모(요청 자신)
            body = parse_response(msg.get("text", ""), task_id)
            if body is not None:
                return body
        if _clock() >= deadline:
            return None
        _sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(description="Hermes 역방향 검토 브리지")
    parser.add_argument("text", nargs="?", help="요청 본문 (또는 --file)")
    parser.add_argument("--mode", required=True, choices=VALID_MODES,
                        help="question(/hermes 질문:) 또는 verify(/hermes 검증:)")
    parser.add_argument("--file", help="요청 본문 파일 경로 (utf-8)")
    args = parser.parse_args()

    load_env(ROOT / ".env")
    token = require_env("SLACK_BOT_TOKEN")
    channel = require_env("HERMES_SLACK_CHANNEL")

    if args.file:
        body = Path(args.file).read_text(encoding="utf-8").strip()
    elif args.text:
        body = args.text.strip()
    else:
        sys.exit("[hermes_bridge] 요청 본문 없음 — 텍스트 인자 또는 --file 지정")
    if not body:
        sys.exit("[hermes_bridge] 빈 요청은 보내지 않음")

    task_id = new_task_id()
    request_text = build_request(task_id, args.mode, body)

    try:
        thread_ts = post_request(token, channel, request_text)
    except (requests.RequestException, BridgeError) as e:
        print(f"BLOCK: 단계=요청전송(chat.postMessage) task_id={task_id} — {e} (재전송 안 함)")
        sys.exit(2)

    print(f"[hermes_bridge] 요청 전송됨 task_id={task_id} mode={args.mode} "
          f"— 스레드 응답 대기 (interval={POLL_INTERVAL_SEC}s, timeout={POLL_TIMEOUT_SEC}s)",
          file=sys.stderr)

    try:
        response_body = wait_response(
            token, channel, thread_ts, task_id,
            timeout=POLL_TIMEOUT_SEC, interval=POLL_INTERVAL_SEC,
        )
    except (requests.RequestException, BridgeError) as e:
        print(f"BLOCK: 단계=응답조회(conversations.replies) task_id={task_id} — {e} (재전송 안 함)")
        sys.exit(2)

    if response_body is None:
        print(f"HOLD: 단계=응답대기 timeout({int(POLL_TIMEOUT_SEC)}s) task_id={task_id} "
              f"— 응답 없음, 같은 task ID 재전송 안 함")
        sys.exit(3)

    print(response_body)


if __name__ == "__main__":
    main()
