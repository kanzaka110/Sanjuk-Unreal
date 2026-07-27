"""Tests for scripts/hermes_bridge.py — Hermes 역방향 검토 브리지.

검증 항목 (RED→GREEN):
1. 요청 생성 — hreq_ task ID + [HERMES-REQUEST v1] 정확한 포맷
2. task ID 불일치 / 마커 없는 메시지 무시
3. 동일 스레드 응답 회수 (conversations.replies)
4. timeout 시 같은 task ID 무재전송 (chat.postMessage 1회)
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import hermes_bridge as hb


class FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


def make_response_text(task_id: str, body: str) -> str:
    return f"[HERMES-RESPONSE v1]\ntask_id: {task_id}\nbody:\n{body}"


class TestRequestBuild:
    def test_task_id_prefix_and_uniqueness(self):
        first = hb.new_task_id()
        second = hb.new_task_id()
        assert first.startswith("hreq_")
        assert second.startswith("hreq_")
        assert first != second

    def test_build_request_exact_format_question(self):
        text = hb.build_request("hreq_abc123", "question", "질문 본문\n둘째 줄")
        assert text == (
            "[HERMES-REQUEST v1]\n"
            "task_id: hreq_abc123\n"
            "mode: question\n"
            "domain: ue-sb2\n"
            "reply_required: true\n"
            "body:\n"
            "질문 본문\n둘째 줄"
        )

    def test_build_request_verify_mode(self):
        text = hb.build_request("hreq_v1", "verify", "검증 본문")
        assert "mode: verify\n" in text
        assert text.startswith("[HERMES-REQUEST v1]\n")

    def test_build_request_rejects_unknown_mode(self):
        with pytest.raises(ValueError):
            hb.build_request("hreq_x", "digest", "본문")

    def test_poll_constants(self):
        assert hb.POLL_INTERVAL_SEC == 3.0
        assert hb.POLL_TIMEOUT_SEC == 180.0


class TestParseResponse:
    def test_matching_response_returns_body(self):
        text = make_response_text("hreq_match1", "답변 본문\n둘째 줄")
        assert hb.parse_response(text, "hreq_match1") == "답변 본문\n둘째 줄"

    def test_task_id_mismatch_ignored(self):
        text = make_response_text("hreq_other9", "다른 요청 답변")
        assert hb.parse_response(text, "hreq_match1") is None

    def test_task_id_prefix_collision_ignored(self):
        # hreq_match1 요청에 hreq_match12 응답이 매칭되면 안 됨 (정확 일치)
        text = make_response_text("hreq_match12", "본문")
        assert hb.parse_response(text, "hreq_match1") is None

    def test_plain_bot_message_ignored(self):
        assert hb.parse_response("[LOCAL-CLAUDE]\n일반 자동공유 메시지", "hreq_x") is None
        assert hb.parse_response("그냥 봇 메시지 task_id: hreq_x", "hreq_x") is None

    def test_request_echo_ignored(self):
        # 요청 자신([HERMES-REQUEST v1])은 응답으로 취급하지 않음
        text = hb.build_request("hreq_x", "question", "본문")
        assert hb.parse_response(text, "hreq_x") is None


class TestThreadRecovery:
    def test_reply_in_same_thread_recovered(self, monkeypatch):
        seen_params = []

        def fake_get(url, headers=None, params=None, timeout=None):
            seen_params.append((url, dict(params)))
            return FakeResponse({
                "ok": True,
                "messages": [
                    {"ts": "111.000", "text": "[HERMES-REQUEST v1]\ntask_id: hreq_t1\n..."},
                    {"ts": "111.001", "text": make_response_text("hreq_zzz", "다른 task 응답")},
                    {"ts": "111.002", "text": make_response_text("hreq_t1", "정답 본문")},
                ],
            })

        monkeypatch.setattr(hb.requests, "get", fake_get)
        body = hb.wait_response(
            "tok", "CH", "111.000", "hreq_t1",
            timeout=10, interval=0, _sleep=lambda s: None,
        )
        assert body == "정답 본문"
        url, params = seen_params[0]
        assert url.endswith("conversations.replies")
        assert params["channel"] == "CH"
        assert params["ts"] == "111.000"  # 저장한 부모 ts로 같은 스레드 조회

    def test_only_mismatched_replies_returns_none(self, monkeypatch):
        def fake_get(url, headers=None, params=None, timeout=None):
            return FakeResponse({
                "ok": True,
                "messages": [
                    {"ts": "111.001", "text": make_response_text("hreq_other", "무관 응답")},
                ],
            })

        monkeypatch.setattr(hb.requests, "get", fake_get)
        clock = iter([0.0, 1.0, 2.0, 3.0, 4.0])
        body = hb.wait_response(
            "tok", "CH", "111.000", "hreq_t1",
            timeout=3, interval=1, _sleep=lambda s: None, _clock=lambda: next(clock),
        )
        assert body is None


class TestTimeoutNoResend:
    def test_timeout_posts_once_and_holds(self, monkeypatch, capsys):
        post_calls = []

        def fake_post(url, headers=None, json=None, timeout=None):
            post_calls.append((url, dict(json)))
            return FakeResponse({"ok": True, "ts": "222.000"})

        def fake_get(url, headers=None, params=None, timeout=None):
            return FakeResponse({"ok": True, "messages": []})

        monkeypatch.setattr(hb.requests, "post", fake_post)
        monkeypatch.setattr(hb.requests, "get", fake_get)
        monkeypatch.setattr(hb, "POLL_TIMEOUT_SEC", 0.0)
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
        monkeypatch.setenv("HERMES_SLACK_CHANNEL", "CTEST")
        monkeypatch.setattr(sys, "argv", ["hermes_bridge.py", "--mode", "question", "본문"])

        with pytest.raises(SystemExit) as exc:
            hb.main()

        assert exc.value.code != 0
        assert len(post_calls) == 1  # 같은 task ID 재전송 없음
        out = capsys.readouterr().out
        assert "HOLD" in out
        assert "재전송" in out

    def test_api_error_blocks_without_resend(self, monkeypatch, capsys):
        post_calls = []

        def fake_post(url, headers=None, json=None, timeout=None):
            post_calls.append(url)
            return FakeResponse({"ok": False, "error": "channel_not_found"})

        monkeypatch.setattr(hb.requests, "post", fake_post)
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
        monkeypatch.setenv("HERMES_SLACK_CHANNEL", "CTEST")
        monkeypatch.setattr(sys, "argv", ["hermes_bridge.py", "--mode", "question", "본문"])

        with pytest.raises(SystemExit) as exc:
            hb.main()

        assert exc.value.code != 0
        assert len(post_calls) == 1
        out = capsys.readouterr().out
        assert "BLOCK" in out
        assert "chat.postMessage" in out  # 실패 단계 명시
        assert "xoxb-test" not in out  # 토큰 미출력
