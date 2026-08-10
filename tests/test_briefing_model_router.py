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


def test_success_uses_provider_policy_and_writes_sanitized_v2_lineage(tmp_path):
    calls = []

    def fake(prompt, **kwargs):
        calls.append((prompt, kwargs))
        return "ok"

    lineage = tmp_path / "usage-v2.jsonl"
    with router.briefing_model_session("UE_SCHEDULED", lineage_path=lineage, run_id="run-1"):
        assert router.route_current("PUBLIC_RESEARCH", "public Epic UE release notes", _executor=fake) == "ok"

    assert calls[0][1]["provider"] == "perplexity"
    assert calls[0][1]["authority"] == "public_evidence"
    record = json.loads(lineage.read_text(encoding="utf-8"))
    assert record["schema_version"] == 2
    assert record["policy_version"] == router.POLICY_VERSION
    assert record["stage"] == "PUBLIC_RESEARCH"
    assert "public Epic UE release notes" not in lineage.read_text(encoding="utf-8")


def test_provider_failure_is_fail_closed_without_fallback(tmp_path):
    calls = 0

    def fake(_prompt, **_kwargs):
        nonlocal calls
        calls += 1
        return ""

    with router.briefing_model_session("UE_SCHEDULED", lineage_path=tmp_path / "usage-v2.jsonl"):
        with pytest.raises(router.RoutingRefusal, match="provider_call_failed"):
            router.route_current("BODY_GENERATION", "public technical facts", _executor=fake)
    assert calls == 1
    assert router.POLICY["stages"]["BODY_GENERATION"]["fallback"] is None


def test_sensitive_public_input_refuses_before_spawn(tmp_path):
    calls = 0

    def fake(_prompt, **_kwargs):
        nonlocal calls
        calls += 1
        return "ok"

    with router.briefing_model_session("UE_SCHEDULED", lineage_path=tmp_path / "usage-v2.jsonl"):
        with pytest.raises(router.RoutingRefusal, match="sensitive_public_payload"):
            router.route_current("PUBLIC_RESEARCH", "read the Perforce project path", _executor=fake)
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
    assert calls == 1


def test_grok_provider_flag_has_explicit_value():
    source = (UE_BOT / "briefing_grok_cli.py").read_text(encoding="utf-8")
    assert '"--provider",\n        _PROVIDER,\n        "-m",' in source
