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


def test_success_uses_policy_and_writes_sanitized_lineage(tmp_path):
    calls = []

    def fake(prompt, **kwargs):
        calls.append((prompt, kwargs))
        return "ok"

    lineage = tmp_path / "usage.jsonl"
    with router.briefing_model_session("UE_SCHEDULED", lineage_path=lineage, run_id="run-1"):
        assert router.route_current("PUBLIC_RESEARCH", "secret prompt", _executor=fake) == "ok"

    assert calls[0][1]["model"] == "sonnet"
    record = json.loads(lineage.read_text(encoding="utf-8"))
    assert record["policy_version"] == router.POLICY_VERSION
    assert record["stage"] == "PUBLIC_RESEARCH"
    assert record["outcome"] == "success"
    assert "secret prompt" not in lineage.read_text(encoding="utf-8")


def test_quota_allows_exactly_one_declared_fallback(tmp_path, monkeypatch):
    models = []

    def fake(_prompt, **kwargs):
        models.append(kwargs["model"])
        return "" if len(models) == 1 else "fallback-ok"

    monkeypatch.setattr(router, "get_last_failure_reason", lambda: "quota")
    with router.briefing_model_session("UE_SCHEDULED", lineage_path=tmp_path / "usage.jsonl"):
        assert router.route_current("BODY_GENERATION", "p", _executor=fake) == "fallback-ok"

    assert models == ["sonnet", "haiku"]


def test_non_quota_failure_is_fail_closed_without_fallback(tmp_path, monkeypatch):
    calls = 0

    def fake(_prompt, **_kwargs):
        nonlocal calls
        calls += 1
        return ""

    monkeypatch.setattr(router, "get_last_failure_reason", lambda: "timeout")
    with router.briefing_model_session("UE_SCHEDULED", lineage_path=tmp_path / "usage.jsonl"):
        with pytest.raises(router.RoutingRefusal, match="timeout"):
            router.route_current("FACT_EXTRACTION", "p", _executor=fake)
    assert calls == 1


def test_stage_cap_refuses_before_extra_spawn(tmp_path, monkeypatch):
    policy = deepcopy(router.POLICY)
    policy["stages"]["PUBLIC_RESEARCH"]["max_calls"] = 1
    monkeypatch.setattr(router, "POLICY", policy)
    calls = 0

    def fake(_prompt, **_kwargs):
        nonlocal calls
        calls += 1
        return "ok"

    with router.briefing_model_session("UE_SCHEDULED", lineage_path=tmp_path / "usage.jsonl"):
        assert router.route_current("PUBLIC_RESEARCH", "one", _executor=fake) == "ok"
        with pytest.raises(router.RoutingRefusal, match="stage_cap_exceeded"):
            router.route_current("PUBLIC_RESEARCH", "two", _executor=fake)
    assert calls == 1
