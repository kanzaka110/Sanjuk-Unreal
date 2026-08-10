"""Provider-separated, bounded routing for scheduled public UE briefings."""
from __future__ import annotations

import contextvars
import json
import os
import re
import unicodedata
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterator

POLICY_VERSION = "unreal-briefing-model-router.v2"
DEFAULT_STATE_DIR = Path("/home/kanzaka110/.local/state/sanjuk-briefing-router/unreal")
POLICY = {
    "policy_version": POLICY_VERSION,
    "run_total_cap": 36,
    "stages": {
        "PUBLIC_RESEARCH": {"provider": "perplexity", "role": "public_evidence", "model": "sonar-search", "authority": "public_evidence", "timeout": 20, "max_calls": 6, "fallback": None},
        "FACT_EXTRACTION": {"provider": "codex", "role": "technical_extract", "model": "gpt-5.6-sol", "authority": "public_editorial", "timeout": 300, "max_calls": 16, "fallback": None},
        "TREND_ANALYSIS": {"provider": "grok", "role": "public_trend", "model": "grok-build-0.1", "authority": "public_analysis", "timeout": 180, "max_calls": 6, "fallback": None},
        "CROSS_ANALYSIS": {"provider": "grok", "role": "public_cross_analysis", "model": "grok-build-0.1", "authority": "public_analysis", "timeout": 180, "max_calls": 2, "fallback": None},
        "METADATA": {"provider": "codex", "role": "structured_metadata", "model": "gpt-5.6-sol", "authority": "public_editorial", "timeout": 300, "max_calls": 6, "fallback": None},
        "BODY_GENERATION": {"provider": "codex", "role": "technical_editorial", "model": "gpt-5.6-sol", "authority": "public_editorial", "timeout": 300, "max_calls": 6, "fallback": None},
    },
}
_SENSITIVE = re.compile(r"api[_ -]?key|token|secret|password|credential|account|holdings?|broker|order|계좌|예수금|평단|주문|perforce|confluence|e:\\|c:\\", re.I)


class RoutingRefusal(RuntimeError):
    pass


@dataclass
class BriefingModelSession:
    run_id: str
    briefing_type: str
    lineage_path: Path
    total_calls: int = 0
    stage_calls: dict[str, int] = field(default_factory=dict)
    provider_calls: dict[str, int] = field(default_factory=dict)
    sensitive_rejections: int = 0


_CURRENT_SESSION: contextvars.ContextVar[BriefingModelSession | None] = contextvars.ContextVar("ue_briefing_model_session_v2", default=None)


def assert_public_content(text: str) -> None:
    normalized = " ".join(unicodedata.normalize("NFKC", text).lower().split())
    if not text.strip() or len(text) > 16000:
        raise ValueError("payload_invalid")
    if _SENSITIVE.search(normalized):
        raise ValueError("sensitive_public_payload")


def _append(session: BriefingModelSession, **fields: object) -> None:
    record = {
        "schema_version": 2,
        "policy_version": POLICY_VERSION,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "run_id": session.run_id,
        "briefing_type": session.briefing_type[:64],
        "fallback_used": False,
        **fields,
    }
    session.lineage_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(session.lineage_path.parent, 0o700)
    fd = os.open(session.lineage_path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        os.write(fd, (json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n").encode())
        os.fsync(fd)
    finally:
        os.close(fd)


def _default_executor(prompt: str, **kwargs: object) -> str:
    provider = str(kwargs["provider"])
    if provider == "perplexity":
        from briefing_perplexity import search_public
        return search_public(prompt, before_transport=kwargs.get("before_transport"), state_dir=kwargs.get("state_dir"), timeout=int(str(kwargs["timeout"])))
    if provider == "grok":
        from briefing_grok_cli import grok_cli
        return grok_cli(prompt, timeout=int(str(kwargs["timeout"])))
    if provider == "codex":
        from briefing_codex_cli import codex_cli
        return codex_cli(prompt, timeout=int(str(kwargs["timeout"])))
    raise RoutingRefusal("provider_not_allowed")


def route_current(stage: str, prompt: str, *, _executor: Callable[..., str] | None = None, **kwargs: object) -> str:
    del kwargs
    session = _CURRENT_SESSION.get()
    if session is None:
        raise RoutingRefusal("briefing_session_missing")
    cfg = POLICY["stages"].get(stage)
    if cfg is None:
        raise RoutingRefusal("stage_not_allowed")
    try:
        assert_public_content(prompt)
    except ValueError as exc:
        session.sensitive_rejections += 1
        _append(session, stage=stage, provider=cfg["provider"], role=cfg["role"], model=cfg["model"], authority=cfg["authority"], reserved=False, cache_hit=False, outcome="refused", reason_code="sensitive_public_payload")
        raise RoutingRefusal("sensitive_public_payload") from exc
    if session.total_calls >= POLICY["run_total_cap"] or session.stage_calls.get(stage, 0) >= cfg["max_calls"]:
        raise RoutingRefusal("stage_cap_exceeded")
    reserved = False

    def reserve() -> None:
        nonlocal reserved
        if reserved:
            return
        if session.total_calls >= POLICY["run_total_cap"] or session.stage_calls.get(stage, 0) >= cfg["max_calls"]:
            raise RoutingRefusal("stage_cap_exceeded")
        session.total_calls += 1
        session.stage_calls[stage] = session.stage_calls.get(stage, 0) + 1
        provider = str(cfg["provider"])
        session.provider_calls[provider] = session.provider_calls.get(provider, 0) + 1
        reserved = True

    executor = _executor or _default_executor
    if _executor is not None or cfg["provider"] != "perplexity":
        reserve()
    try:
        text = executor(prompt, provider=cfg["provider"], model=cfg["model"], authority=cfg["authority"], timeout=cfg["timeout"], state_dir=session.lineage_path.parent, before_transport=reserve)
    except Exception:
        _append(session, stage=stage, provider=cfg["provider"], role=cfg["role"], model=cfg["model"], authority=cfg["authority"], reserved=reserved, cache_hit=False, outcome="failed", reason_code="provider_call_failed")
        raise
    if not isinstance(text, str) or not text.strip():
        raise RoutingRefusal("provider_call_failed")
    _append(session, stage=stage, provider=cfg["provider"], role=cfg["role"], model=cfg["model"], authority=cfg["authority"], reserved=reserved, cache_hit=not reserved, outcome="success", reason_code="")
    return text.strip()


@contextmanager
def briefing_model_session(briefing_type: str, *, lineage_path: str | os.PathLike[str] | None = None, run_id: str | None = None) -> Iterator[BriefingModelSession]:
    path = Path(lineage_path) if lineage_path else DEFAULT_STATE_DIR / "lineage-v2.jsonl"
    session = BriefingModelSession(run_id or uuid.uuid4().hex, briefing_type, path)
    token = _CURRENT_SESSION.set(session)
    try:
        yield session
    finally:
        _CURRENT_SESSION.reset(token)


__all__ = ["POLICY", "POLICY_VERSION", "DEFAULT_STATE_DIR", "BriefingModelSession", "RoutingRefusal", "assert_public_content", "briefing_model_session", "route_current"]
