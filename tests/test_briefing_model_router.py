from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
UE_BOT = ROOT / "UE_bot"
for path in (str(UE_BOT), str(ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

import model_router as router


def _events(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_success_uses_provider_policy_and_writes_sanitized_v3_lineage(tmp_path):
    calls = []

    def fake(prompt, **kwargs):
        calls.append((prompt, kwargs))
        return "ok"

    lineage = tmp_path / "usage-v2.jsonl"
    with router.briefing_model_session("UE_SCHEDULED", lineage_path=lineage, run_id="run-1"):
        assert router.route_current("PUBLIC_RESEARCH", "public Epic UE release notes", _executor=fake) == "ok"
        router.record_delivery(success=True, attempts=1)

    assert calls[0][1]["provider"] == "perplexity"
    assert calls[0][1]["authority"] == "public_evidence"
    events = _events(lineage)
    assert all(record["schema_version"] == 3 for record in events)
    assert all(record["policy_version"] == router.POLICY_VERSION for record in events)
    assert all(record["run_id"] == "run-1" for record in events)
    assert all(len(record["repo_commit"]) == 40 for record in events)
    assert len([row for row in events if row["event_type"] == "delivery_terminal"]) == 1
    summary = [row for row in events if row["event_type"] == "run_summary"]
    assert len(summary) == 1
    assert summary[0]["fallback_count"] == 0
    assert summary[0]["outbound_sensitive_count"] == 0
    assert summary[0]["order_authority_invocations"] == 0
    assert "public Epic UE release notes" not in lineage.read_text(encoding="utf-8")


def test_natural_default_provider_caps_are_enforced_before_tenth_codex_call(tmp_path):
    def fake(_prompt, **_kwargs):
        return "ok"

    with router.briefing_model_session(
        "UE_SCHEDULED", lineage_path=tmp_path / "usage.jsonl", natural_default=True,
    ):
        for _ in range(3):
            router.route_current("PUBLIC_RESEARCH", "public UE evidence", _executor=fake)
        for _ in range(3):
            router.route_current("TREND_ANALYSIS", "public UE trend", _executor=fake)
        router.route_current("CROSS_ANALYSIS", "public UE cross", _executor=fake)
        for _ in range(3):
            router.route_current("FACT_EXTRACTION", "public UE facts", _executor=fake)
            router.route_current("METADATA", "public UE metadata", _executor=fake)
            router.route_current("BODY_GENERATION", "public UE body", _executor=fake)
        with pytest.raises(router.RoutingRefusal, match="stage_cap_exceeded"):
            router.route_current("METADATA", "public UE extra", _executor=fake)
        router.record_delivery(success=True, attempts=1)

    summary = [row for row in _events(tmp_path / "usage.jsonl") if row["event_type"] == "run_summary"][0]
    assert summary["provider_call_counts"] == {"perplexity": 3, "grok": 4, "codex": 9}
    assert summary["total_calls"] == 16


def test_provider_failure_is_fail_closed_without_fallback(tmp_path):
    calls = 0

    def fake(_prompt, **_kwargs):
        nonlocal calls
        calls += 1
        return ""

    lineage = tmp_path / "usage-v2.jsonl"
    with pytest.raises(router.RoutingRefusal, match="provider_call_failed"):
        with router.briefing_model_session("UE_SCHEDULED", lineage_path=lineage):
            router.route_current("BODY_GENERATION", "public technical facts", _executor=fake)
    assert calls == 1
    assert router.POLICY["stages"]["BODY_GENERATION"]["fallback"] is None
    events = _events(lineage)
    assert len([row for row in events if row["event_type"] == "delivery_terminal"]) == 1
    assert len([row for row in events if row["event_type"] == "run_summary"]) == 1


def test_sensitive_public_input_refuses_before_spawn(tmp_path):
    calls = 0

    def fake(_prompt, **_kwargs):
        nonlocal calls
        calls += 1
        return "ok"

    with router.briefing_model_session("UE_SCHEDULED", lineage_path=tmp_path / "usage-v2.jsonl"):
        with pytest.raises(router.RoutingRefusal, match="sensitive_public_payload"):
            router.route_current("PUBLIC_RESEARCH", "read the Perforce project path", _executor=fake)
        router.record_delivery(success=False, reason_code="content_refused", attempts=0)
    assert calls == 0


def test_stage_cap_refuses_before_extra_spawn(tmp_path, monkeypatch):
    policy = deepcopy(router.POLICY)
    policy["stages"]["PUBLIC_RESEARCH"]["max_calls"] = 1
    monkeypatch.setattr(router, "POLICY", policy)
    calls = 0

    def fake(_prompt, **_kwargs):
        nonlocal calls
        calls += 1
        return "ok"

    with router.briefing_model_session("UE_SCHEDULED", lineage_path=tmp_path / "usage-v2.jsonl"):
        assert router.route_current("PUBLIC_RESEARCH", "public one", _executor=fake) == "ok"
        with pytest.raises(router.RoutingRefusal, match="stage_cap_exceeded"):
            router.route_current("PUBLIC_RESEARCH", "public two", _executor=fake)
        router.record_delivery(success=True, attempts=1)
    assert calls == 1


def test_telegram_sender_returns_structured_terminal_result(monkeypatch):
    import briefing_telegram

    class Response:
        status_code = 200

        def json(self):
            return {"ok": True}

    monkeypatch.setattr(briefing_telegram.requests, "post", lambda *_args, **_kwargs: Response())
    result = briefing_telegram.send_telegram([], bot_token="token", chat_id="chat", notion_db_id="db")
    assert result == {"success": True, "reason_code": "", "attempts": 1}


def test_grok_provider_flag_has_explicit_value():
    source = (UE_BOT / "briefing_grok_cli.py").read_text(encoding="utf-8")
    assert '"--provider",\n        _PROVIDER,\n        "-m",' in source
