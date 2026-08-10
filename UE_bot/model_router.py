"""Versioned, bounded model routing for scheduled UE briefings."""

from __future__ import annotations

import json
import os
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Callable, Iterator

from shared_config import claude_cli, get_last_failure_reason

POLICY_VERSION = "briefing-model-router.v1"
POLICY = {
    "policy_version": POLICY_VERSION,
    "run_total_cap": 32,
    "stages": {
        "PUBLIC_RESEARCH": {
            "role": "public_research", "model": "sonnet", "timeout": 300,
            "effort": "medium", "max_calls": 6,
            "fallback": {"role": "public_research_fallback", "model": "haiku"},
        },
        "FACT_EXTRACTION": {
            "role": "structured_extract", "model": "haiku", "timeout": 60,
            "effort": "low", "max_calls": 16,
            "fallback": {"role": "structured_extract_fallback", "model": "sonnet"},
        },
        "TREND_ANALYSIS": {
            "role": "trend_analysis", "model": "sonnet", "timeout": 120,
            "effort": "medium", "max_calls": 6,
            "fallback": {"role": "trend_analysis_fallback", "model": "haiku"},
        },
        "CROSS_ANALYSIS": {
            "role": "cross_analysis", "model": "sonnet", "timeout": 120,
            "effort": "medium", "max_calls": 2,
            "fallback": {"role": "cross_analysis_fallback", "model": "haiku"},
        },
        "METADATA": {
            "role": "structured_metadata", "model": "haiku", "timeout": 120,
            "effort": "high", "max_calls": 6,
            "fallback": {"role": "structured_metadata_fallback", "model": "sonnet"},
        },
        "BODY_GENERATION": {
            "role": "educational_synthesis", "model": "sonnet", "timeout": 300,
            "effort": "high", "max_calls": 6,
            "fallback": {"role": "educational_synthesis_fallback", "model": "haiku"},
        },
    },
}

_FALLBACK_REASONS = frozenset({"quota", "unavailable"})
_DEFAULT_LINEAGE_PATH = Path(__file__).resolve().parent / "data" / "briefing_model_usage.jsonl"


class RoutingRefusal(RuntimeError):
    """A routing decision was refused before any unapproved model call."""


@dataclass
class BriefingModelSession:
    run_id: str
    briefing_type: str
    lineage_path: Path
    total_calls: int = 0
    stage_calls: dict[str, int] = field(default_factory=dict)
    lock: Lock = field(default_factory=Lock, repr=False)


_CURRENT_SESSION: ContextVar[BriefingModelSession | None] = ContextVar(
    "ue_briefing_model_session", default=None,
)


def _validate_policy() -> None:
    if POLICY.get("policy_version") != POLICY_VERSION:
        raise RoutingRefusal("policy_version_invalid")
    if not isinstance(POLICY.get("run_total_cap"), int) or POLICY["run_total_cap"] < 1:
        raise RoutingRefusal("run_total_cap_invalid")
    for stage, cfg in POLICY.get("stages", {}).items():
        required = ("role", "model", "timeout", "effort", "max_calls", "fallback")
        if not stage or any(key not in cfg for key in required):
            raise RoutingRefusal("stage_policy_invalid")
        if not isinstance(cfg["max_calls"], int) or cfg["max_calls"] < 1:
            raise RoutingRefusal("stage_cap_invalid")


def _append_lineage(session: BriefingModelSession, **fields: object) -> None:
    record = {
        "schema_version": 1,
        "policy_version": POLICY_VERSION,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "run_id": session.run_id,
        "briefing_type": session.briefing_type[:64],
        **fields,
    }
    try:
        session.lineage_path.parent.mkdir(parents=True, exist_ok=True)
        payload = (json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        fd = os.open(session.lineage_path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
        try:
            os.write(fd, payload)
        finally:
            os.close(fd)
    except OSError:
        pass


def _reserve(session: BriefingModelSession, stage: str, cfg: dict) -> None:
    refusal = ""
    with session.lock:
        stage_count = session.stage_calls.get(stage, 0)
        if session.total_calls >= POLICY["run_total_cap"]:
            refusal = "run_cap_exceeded"
        elif stage_count >= cfg["max_calls"]:
            refusal = "stage_cap_exceeded"
        else:
            session.total_calls += 1
            session.stage_calls[stage] = stage_count + 1
    if refusal:
        _append_lineage(session, stage=stage, role=cfg["role"], model="", outcome="refused", reason_code=refusal, fallback_used=False)
        raise RoutingRefusal(refusal)


def _invoke(
    session: BriefingModelSession,
    stage: str,
    cfg: dict,
    prompt: str,
    *,
    role: str,
    model: str,
    fallback_used: bool,
    executor: Callable[..., str],
    kwargs: dict,
) -> tuple[str, str]:
    _reserve(session, stage, cfg)
    text = executor(
        prompt,
        model=model,
        timeout=cfg["timeout"],
        effort=cfg["effort"],
        **kwargs,
    )
    reason = "" if text else (get_last_failure_reason() or "empty_output")
    _append_lineage(
        session, stage=stage, role=role, model=model,
        outcome="success" if text else "failed",
        reason_code="ok" if text else reason,
        fallback_used=fallback_used,
    )
    return text, reason


def route_current(
    stage: str,
    prompt: str,
    *,
    _executor: Callable[..., str] | None = None,
    **kwargs: object,
) -> str:
    """Route one scheduled-briefing model call under the active run policy."""
    _validate_policy()
    session = _CURRENT_SESSION.get()
    if session is None:
        raise RoutingRefusal("briefing_session_missing")
    cfg = POLICY["stages"].get(stage)
    if cfg is None:
        raise RoutingRefusal("stage_not_allowed")
    executor = _executor or claude_cli
    text, reason = _invoke(
        session, stage, cfg, prompt,
        role=cfg["role"], model=cfg["model"], fallback_used=False,
        executor=executor, kwargs=dict(kwargs),
    )
    if text:
        return text
    fallback = cfg.get("fallback")
    if reason not in _FALLBACK_REASONS or not fallback:
        raise RoutingRefusal(f"model_call_refused:{reason}")
    text, fallback_reason = _invoke(
        session, stage, cfg, prompt,
        role=fallback["role"], model=fallback["model"], fallback_used=True,
        executor=executor, kwargs=dict(kwargs),
    )
    if not text:
        raise RoutingRefusal(f"fallback_failed:{fallback_reason}")
    return text


@contextmanager
def briefing_model_session(
    briefing_type: str,
    *,
    lineage_path: str | os.PathLike[str] | None = None,
    run_id: str | None = None,
) -> Iterator[BriefingModelSession]:
    _validate_policy()
    session = BriefingModelSession(
        run_id=run_id or uuid.uuid4().hex,
        briefing_type=briefing_type,
        lineage_path=Path(lineage_path) if lineage_path else _DEFAULT_LINEAGE_PATH,
    )
    token = _CURRENT_SESSION.set(session)
    try:
        yield session
    finally:
        _CURRENT_SESSION.reset(token)


__all__ = [
    "POLICY", "POLICY_VERSION", "BriefingModelSession", "RoutingRefusal",
    "briefing_model_session", "route_current",
]
