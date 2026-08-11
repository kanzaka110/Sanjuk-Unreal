"""Provider-separated, bounded routing, delivery and lineage for scheduled UE briefings."""
from __future__ import annotations

import contextvars
import json
import os
import re
import subprocess
import unicodedata
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterator

POLICY_VERSION = "unreal-briefing-model-router.v3"
DEFAULT_STATE_DIR = Path("/home/kanzaka110/.local/state/sanjuk-briefing-router/unreal")
_REPO_ROOT = Path(__file__).resolve().parents[1]
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
POLICY = {
    "policy_version": POLICY_VERSION,
    "run_total_cap": 36,
    "provider_caps": {"perplexity": 6, "grok": 8, "codex": 28},
    "natural_default_total_cap": 16,
    "natural_default_provider_caps": {"perplexity": 3, "grok": 4, "codex": 9},
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
    repo_commit: str
    natural_default: bool = False
    total_calls: int = 0
    stage_calls: dict[str, int] = field(default_factory=dict)
    provider_calls: dict[str, int] = field(default_factory=dict)
    sensitive_rejections: int = 0
    fallback_count: int = 0
    outbound_sensitive_count: int = 0
    order_authority_invocations: int = 0
    delivery_recorded: bool = False
    delivery_success: bool = False
    delivery_attempts: int = 0
    summary_recorded: bool = False


_CURRENT_SESSION: contextvars.ContextVar[BriefingModelSession | None] = contextvars.ContextVar("ue_briefing_model_session_v3", default=None)


def _repo_commit(repo_root: Path = _REPO_ROOT) -> str:
    try:
        value = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"], check=True,
            capture_output=True, text=True, timeout=10,
        ).stdout.strip().lower()
    except Exception as exc:
        raise RoutingRefusal("repo_commit_unavailable") from exc
    if not _COMMIT_RE.fullmatch(value):
        raise RoutingRefusal("repo_commit_invalid")
    return value


def assert_public_content(text: str) -> None:
    normalized = " ".join(unicodedata.normalize("NFKC", text).lower().split())
    if not text.strip() or len(text) > 16000:
        raise ValueError("payload_invalid")
    if _SENSITIVE.search(normalized):
        raise ValueError("sensitive_public_payload")


def _append(session: BriefingModelSession, **fields: object) -> None:
    record = {
        "schema_version": 3,
        "policy_version": POLICY_VERSION,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "run_id": session.run_id,
        "repo_commit": session.repo_commit,
        "briefing_type": session.briefing_type[:64],
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


def _summary(session: BriefingModelSession) -> dict[str, object]:
    return {
        "provider_call_counts": dict(session.provider_calls),
        "stage_call_counts": dict(session.stage_calls),
        "total_calls": session.total_calls,
        "sensitive_rejection_count": session.sensitive_rejections,
        "fallback_count": session.fallback_count,
        "outbound_sensitive_count": session.outbound_sensitive_count,
        "order_authority_invocations": session.order_authority_invocations,
        "delivery_success": session.delivery_success,
        "delivery_attempts": session.delivery_attempts,
    }


def record_delivery(*, success: bool, reason_code: str = "", attempts: int = 1) -> None:
    session = _CURRENT_SESSION.get()
    if session is None:
        raise RoutingRefusal("briefing_session_missing")
    if session.delivery_recorded:
        raise RoutingRefusal("delivery_already_recorded")
    if attempts < 0:
        raise RoutingRefusal("delivery_attempts_invalid")
    session.delivery_recorded = True
    session.delivery_success = bool(success)
    session.delivery_attempts = int(attempts)
    _append(
        session, event_type="delivery_terminal", channel="telegram",
        outcome="success" if success else "failed",
        reason_code="" if success else (reason_code or "telegram_delivery_failed"),
        attempts=int(attempts),
    )


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
        _append(session, event_type="provider_call", stage=stage, provider=cfg["provider"], role=cfg["role"], model=cfg["model"], authority=cfg["authority"], reserved=False, cache_hit=False, outcome="refused", reason_code="sensitive_public_payload")
        raise RoutingRefusal("sensitive_public_payload") from exc
    provider = str(cfg["provider"])
    total_cap = POLICY["natural_default_total_cap"] if session.natural_default else POLICY["run_total_cap"]
    provider_caps = POLICY["natural_default_provider_caps"] if session.natural_default else POLICY["provider_caps"]
    if session.total_calls >= total_cap or session.stage_calls.get(stage, 0) >= cfg["max_calls"] or session.provider_calls.get(provider, 0) >= provider_caps[provider]:
        raise RoutingRefusal("stage_cap_exceeded")
    reserved = False

    def reserve() -> None:
        nonlocal reserved
        if reserved:
            return
        try:
            assert_public_content(prompt)
        except ValueError as exc:
            session.outbound_sensitive_count += 1
            raise RoutingRefusal("sensitive_public_payload") from exc
        if session.total_calls >= total_cap or session.stage_calls.get(stage, 0) >= cfg["max_calls"] or session.provider_calls.get(provider, 0) >= provider_caps[provider]:
            raise RoutingRefusal("stage_cap_exceeded")
        session.total_calls += 1
        session.stage_calls[stage] = session.stage_calls.get(stage, 0) + 1
        session.provider_calls[provider] = session.provider_calls.get(provider, 0) + 1
        reserved = True

    executor = _executor or _default_executor
    if _executor is not None or provider != "perplexity":
        reserve()
    try:
        text = executor(prompt, provider=provider, model=cfg["model"], authority=cfg["authority"], timeout=cfg["timeout"], state_dir=session.lineage_path.parent, before_transport=reserve)
    except Exception:
        _append(session, event_type="provider_call", stage=stage, provider=provider, role=cfg["role"], model=cfg["model"], authority=cfg["authority"], reserved=reserved, cache_hit=False, outcome="failed", reason_code="provider_call_failed")
        raise
    if not isinstance(text, str) or not text.strip():
        raise RoutingRefusal("provider_call_failed")
    _append(session, event_type="provider_call", stage=stage, provider=provider, role=cfg["role"], model=cfg["model"], authority=cfg["authority"], reserved=reserved, cache_hit=not reserved, outcome="success", reason_code="")
    return text.strip()


@contextmanager
def briefing_model_session(
    briefing_type: str, *, lineage_path: str | os.PathLike[str] | None = None,
    run_id: str | None = None, repo_root: str | os.PathLike[str] | None = None,
    natural_default: bool = False,
) -> Iterator[BriefingModelSession]:
    path = Path(lineage_path) if lineage_path else DEFAULT_STATE_DIR / "lineage-v2.jsonl"
    session = BriefingModelSession(
        run_id or uuid.uuid4().hex, briefing_type, path,
        _repo_commit(Path(repo_root) if repo_root else _REPO_ROOT), bool(natural_default),
    )
    token = _CURRENT_SESSION.set(session)
    try:
        yield session
    finally:
        if not session.delivery_recorded:
            record_delivery(success=False, reason_code="delivery_not_recorded", attempts=0)
        if not session.summary_recorded:
            _append(session, event_type="run_summary", **_summary(session))
            session.summary_recorded = True
        _CURRENT_SESSION.reset(token)


__all__ = ["POLICY", "POLICY_VERSION", "DEFAULT_STATE_DIR", "BriefingModelSession", "RoutingRefusal", "assert_public_content", "briefing_model_session", "record_delivery", "route_current"]
