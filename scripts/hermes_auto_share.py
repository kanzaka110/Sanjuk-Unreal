"""Stop 훅: Claude 턴 종료 시 마지막 응답을 Hermes Slack 봇방으로 자동 전송.

모델 호출 없음 — transcript 파일에서 텍스트만 추출하므로 토큰 소비 0.
훅 stdin으로 {session_id, transcript_path, ...} JSON을 받는다 (Stop 훅 규약).

스레드 구조:
    챗방에는 세션당 부모 메시지 1개 ([LOCAL-CLAUDE] 세션 ... — <첫 요청 요약>)
    매 턴 다이제스트는 그 스레드의 답글로 들어감.
    세션→스레드 ts 매핑: scripts/_hermes_threads.json

필터 (잡담 턴 제외):
    - 마지막 assistant 텍스트가 HERMES_AUTO_MIN_CHARS(기본 300) 미만이면 skip
    - 직전 전송과 동일 내용(해시)이면 skip
    - 서브에이전트(sidechain) 메시지는 무시

실패는 모두 조용히 무시 (exit 0) — 훅이 본 세션을 방해하면 안 됨.
디버그 로그: scripts/_hermes_auto.log
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
HASH_FILE = SCRIPT_DIR / "_hermes_last_hash.txt"
THREADS_FILE = SCRIPT_DIR / "_hermes_threads.json"
LOG_FILE = SCRIPT_DIR / "_hermes_auto.log"
MAX_BODY = 3500
TOPIC_MAX = 100


def log(msg: str) -> None:
    try:
        stamp = datetime.datetime.now().strftime("%m-%d %H:%M:%S")
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(f"[{stamp}] {msg}\n")
    except OSError:
        pass


def iter_entries(transcript_path: Path):
    with transcript_path.open(encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def last_assistant_text(transcript_path: Path) -> str:
    """마지막 assistant 메시지의 text 블록 결합."""
    result = ""
    for entry in iter_entries(transcript_path):
        if entry.get("type") != "assistant" or entry.get("isSidechain"):
            continue
        content = entry.get("message", {}).get("content", [])
        texts = [
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        joined = "\n".join(t for t in texts if t).strip()
        if joined:
            result = joined
    return result


def first_user_topic(transcript_path: Path) -> str:
    """첫 사용자 메시지에서 세션 주제 추출 (한 줄, TOPIC_MAX자)."""
    for entry in iter_entries(transcript_path):
        if entry.get("type") != "user" or entry.get("isSidechain"):
            continue
        content = entry.get("message", {}).get("content", "")
        if isinstance(content, list):
            content = " ".join(
                b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"
            )
        text = " ".join(str(content).split()).strip()
        if not text or text.startswith("<"):  # 커맨드 확장/시스템 주입 스킵
            continue
        return text[:TOPIC_MAX] + ("…" if len(text) > TOPIC_MAX else "")
    return "(주제 미상)"


def load_threads() -> dict:
    if THREADS_FILE.is_file():
        try:
            return json.loads(THREADS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def get_session_thread(
    session_id: str, transcript_path: Path, token: str, channel: str, post_message
) -> str:
    """세션의 부모 메시지 ts 반환 — 없으면 챗방에 부모 게시 후 기록."""
    threads = load_threads()
    ts = threads.get(session_id, "")
    if ts:
        return ts

    stamp = datetime.datetime.now().strftime("%m-%d %H:%M")
    topic = first_user_topic(transcript_path)
    ts = post_message(token, channel, f"[LOCAL-CLAUDE] 세션 {stamp} — {topic}")

    threads[session_id] = ts
    threads["_latest"] = ts  # 수동 /hermes가 현재 스레드에 답글 달 때 사용
    if len(threads) > 60:  # 오래된 세션 정리
        keep = dict(list(threads.items())[-40:])
        keep["_latest"] = threads["_latest"]
        threads = keep
    THREADS_FILE.write_text(json.dumps(threads, ensure_ascii=False, indent=1), encoding="utf-8")
    return ts


def main() -> None:
    try:
        hook_input = json.loads(sys.stdin.buffer.read().decode("utf-8-sig"))
        transcript_path = Path(hook_input.get("transcript_path", ""))
        session_id = hook_input.get("session_id", "unknown")
        if not transcript_path.is_file():
            log(f"skip: transcript 없음 ({transcript_path})")
            return

        sys.path.insert(0, str(SCRIPT_DIR))
        from hermes_send import load_env, post_message, require_env, split_chunks

        load_env(SCRIPT_DIR.parent / ".env")
        min_chars = int(os.environ.get("HERMES_AUTO_MIN_CHARS", "300"))

        text = last_assistant_text(transcript_path)
        if len(text) < min_chars:
            log(f"skip: {len(text)} chars < {min_chars}")
            return

        digest = hashlib.md5(text.encode("utf-8")).hexdigest()
        if HASH_FILE.is_file() and HASH_FILE.read_text(encoding="utf-8").strip() == digest:
            log("skip: 직전 전송과 동일")
            return

        token = require_env("SLACK_BOT_TOKEN")
        channel = require_env("HERMES_SLACK_CHANNEL")

        thread_ts = get_session_thread(session_id, transcript_path, token, channel, post_message)

        body = text[:MAX_BODY] + ("\n…(잘림)" if len(text) > MAX_BODY else "")
        stamp = datetime.datetime.now().strftime("%H:%M")
        message = f"[LOCAL-CLAUDE] {stamp}\n{body}"
        for chunk in split_chunks(message):
            post_message(token, channel, chunk, thread_ts=thread_ts)

        HASH_FILE.write_text(digest, encoding="utf-8")
        log(f"sent: {len(text)} chars → thread {thread_ts}")
    except SystemExit:
        log("skip: env 미설정")
    except Exception as e:  # noqa: BLE001 — 훅은 어떤 실패도 세션을 막으면 안 됨
        log(f"error: {e}")


if __name__ == "__main__":
    main()
