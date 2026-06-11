"""Hermes slack.py 패치: [LOCAL-CLAUDE] self-feed를 observed 컨텍스트로 흡수.

서버에서 실행: /usr/local/lib/hermes-agent/venv/bin/python /tmp/patch_slack.py
"""
PATH = "/usr/local/lib/hermes-agent/gateway/platforms/slack.py"
src = open(PATH, encoding="utf-8").read()

if "_observe_local_claude_feed" in src:
    print("ALREADY_PATCHED")
    raise SystemExit(0)

GATE = '        if event.get("bot_id") or event.get("subtype") == "bot_message":'
assert src.count(GATE) == 1, f"gate anchor count={src.count(GATE)}"

INTERCEPT = GATE + '''
            # [LOCAL-CLAUDE] feed: digests posted with our own bot token from the
            # local Claude Code hook.  Ingest as observed context only -- no
            # dispatch, no reply (custom patch, backup: /root/slack.py.bak-*).
            _feed_text = event.get("text", "") or ""
            if _feed_text.startswith("[LOCAL-CLAUDE]"):
                self._observe_local_claude_feed(event)
                return'''
src = src.replace(GATE, INTERCEPT, 1)

HANDLER = "    async def _handle_slack_message(self, event: dict) -> None:"
assert src.count(HANDLER) == 1, "handler anchor missing"

HELPER = '''    def _observe_local_claude_feed(self, event: dict) -> None:
        """Append a [LOCAL-CLAUDE] self-feed message to its thread session as observed context."""
        store = getattr(self, "_session_store", None)
        if not store:
            return
        try:
            from datetime import datetime, timezone
            channel_id = event.get("channel", "")
            ts = event.get("ts", "")
            thread_ts = event.get("thread_ts", "")
            if not thread_ts and self._dm_top_level_threads_as_sessions():
                thread_ts = ts
            if not channel_id:
                return
            source = self.build_source(
                chat_id=channel_id,
                chat_name=channel_id,
                chat_type="dm",
                user_id="",
                thread_id=thread_ts or None,
            )
            session_entry = store.get_or_create_session(source)
            entry = {
                "role": "user",
                "content": event.get("text", ""),
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                "observed": True,
            }
            if ts:
                entry["message_id"] = str(ts)
            store.append_to_transcript(session_entry.session_id, entry)
            logger.info(
                "[Slack] LOCAL-CLAUDE feed observed: channel=%s thread=%s",
                channel_id, thread_ts or ts,
            )
        except Exception as exc:
            logger.warning("[Slack] Failed to observe LOCAL-CLAUDE feed: %s", exc)

'''
src = src.replace(HANDLER, HELPER + HANDLER, 1)

open(PATH, "w", encoding="utf-8").write(src)
print("PATCHED")
