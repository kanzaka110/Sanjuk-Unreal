#!/usr/bin/env python3
"""Compile authenticated read-only company captures into Evidence Packet bodies.

This module does not authenticate to company systems. An authenticated company-PC
agent reads the source and emits one schema-v2 JSON capture. This compiler then
validates scope/provenance, preserves structured blocks, and hands the resulting
Markdown to the existing byte-preserving packet transport.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import NamedTuple
from urllib.parse import urlparse


class CaptureError(ValueError):
    pass


class CompiledCapture(NamedTuple):
    body: str
    packet_kwargs: dict[str, object]


TOP_KEYS = {
    "schema_version",
    "source",
    "blocks",
    "revisions",
    "claims",
    "conflicts",
    "unresolved",
    "merge_targets",
}
SOURCE_KEYS = {
    "kind",
    "id",
    "title",
    "url",
    "version",
    "updated_at",
    "captured_at",
    "read_only",
    "capture_method",
    "scope",
}
SOURCE_HOSTS = {
    "confluence": {"shiftupcorp.atlassian.net"},
    "drive": {"drive.google.com", "docs.google.com"},
}
EVIDENCE_CLASSES = {
    "CURRENT_MEASUREMENT",
    "HISTORICAL_NOTE",
    "SOURCE_DOCUMENT",
    "CLAUDE_RECORD",
}
SAFE_METHODS = {"confluence_mcp", "drive_readonly", "claude_projector", "ue_readonly_dump"}
SOURCE_METHODS = {
    "confluence": {"confluence_mcp"},
    "drive": {"drive_readonly"},
}
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
SECRET_PATTERNS = (
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"),
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
    re.compile(
        r"(?i)\b(?:api[_ -]?key|password|secret|oauth[_ -]?token|access[_ -]?token)"
        r"\s*[:=]\s*(?!\[REDACTED\])['\"]?[A-Za-z0-9_./+=-]{8,}"
    ),
)


def _text(value: object, name: str, maximum: int = 4000) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise CaptureError(f"{name} is invalid")
    if CONTROL_RE.search(value):
        raise CaptureError(f"{name} contains control characters")
    return value


def _timestamp(value: object, name: str) -> str:
    text = _text(value, name, 64)
    try:
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CaptureError(f"{name} must be ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise CaptureError(f"{name} must include timezone")
    return text


def _string_list(value: object, name: str, *, maximum: int = 1000) -> list[str]:
    if not isinstance(value, list) or len(value) > maximum:
        raise CaptureError(f"{name} must be a bounded list")
    return [_text(item, f"{name} item") for item in value]


def _escape_cell(value: object) -> str:
    text = _text(value, "table cell", 20000)
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("\n", "<br>")


def _render_block(block: object) -> str:
    if not isinstance(block, dict) or "type" not in block:
        raise CaptureError("block is invalid")
    kind = block["type"]
    if kind == "heading":
        if set(block) != {"type", "level", "text"}:
            raise CaptureError("heading block fields invalid")
        level = block["level"]
        if type(level) is not int or not 1 <= level <= 6:
            raise CaptureError("heading level invalid")
        return f"{'#' * level} {_text(block['text'], 'heading text')}"
    if kind == "paragraph":
        if set(block) != {"type", "text"}:
            raise CaptureError("paragraph block fields invalid")
        return _text(block["text"], "paragraph", 100000)
    if kind == "table":
        if set(block) != {"type", "columns", "rows"}:
            raise CaptureError("table block fields invalid")
        columns = _string_list(block["columns"], "table columns", maximum=100)
        rows = block["rows"]
        if not columns or not isinstance(rows, list) or len(rows) > 5000:
            raise CaptureError("table shape invalid")
        rendered = [
            "| " + " | ".join(_escape_cell(item) for item in columns) + " |",
            "| " + " | ".join("---" for _ in columns) + " |",
        ]
        for row in rows:
            if not isinstance(row, list) or len(row) != len(columns):
                raise CaptureError("table row width mismatch")
            rendered.append("| " + " | ".join(_escape_cell(item) for item in row) + " |")
        return "\n".join(rendered)
    if kind == "code":
        if set(block) != {"type", "language", "text"}:
            raise CaptureError("code block fields invalid")
        language = _text(block["language"], "code language", 32)
        if not re.fullmatch(r"[A-Za-z0-9_+.-]{1,32}", language):
            raise CaptureError("code language invalid")
        code = _text(block["text"], "code text", 200000)
        if "```" in code:
            raise CaptureError("code contains reserved fence")
        return f"```{language}\n{code}\n```"
    if kind == "image":
        expected = {"type", "attachment_id", "filename", "caption", "context"}
        if set(block) != expected:
            raise CaptureError("image block fields invalid")
        return "\n".join(
            [
                f"- image attachment_id: `{_text(block['attachment_id'], 'attachment_id', 300)}`",
                f"- filename: `{_text(block['filename'], 'image filename', 500)}`",
                f"- caption: {_text(block['caption'], 'image caption', 5000)}",
                f"- context: {_text(block['context'], 'image context', 20000)}",
            ]
        )
    if kind == "attachment":
        expected = {"type", "attachment_id", "filename", "media_type", "bytes", "sha256"}
        if set(block) != expected:
            raise CaptureError("attachment block fields invalid")
        size = block["bytes"]
        digest = block["sha256"]
        if type(size) is not int or not 0 <= size <= 2_000_000_000:
            raise CaptureError("attachment bytes invalid")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise CaptureError("attachment sha256 invalid")
        return (
            f"- attachment `{_text(block['filename'], 'attachment filename', 500)}` "
            f"(id `{_text(block['attachment_id'], 'attachment_id', 300)}`, "
            f"type `{_text(block['media_type'], 'media_type', 200)}`, bytes `{size}`, sha256 `{digest}`)"
        )
    raise CaptureError(f"unsupported block type: {kind}")


def _validate_allowlist(source: dict[str, object], allowlist: dict[str, object]) -> None:
    if allowlist.get("schema_version") != 1:
        raise CaptureError("allowlist schema_version invalid")
    kind = str(source["kind"])
    section = allowlist.get(kind)
    if not isinstance(section, dict):
        raise CaptureError("source kind disabled by allowlist")
    scope = source["scope"]
    if not isinstance(scope, dict):
        raise CaptureError("source scope invalid")
    if kind == "confluence":
        if set(scope) != {"space"} or scope["space"] not in section.get("spaces", []):
            raise CaptureError("Confluence space outside allowlist")
        page_ids = section.get("page_ids", [])
        if page_ids and source["id"] not in page_ids:
            raise CaptureError("Confluence page outside allowlist")
    elif kind == "drive":
        if set(scope) != {"folder_id"} or scope["folder_id"] not in section.get("folder_ids", []):
            raise CaptureError("Drive folder outside allowlist")


def compile_capture(capture: object, allowlist: object) -> CompiledCapture:
    if not isinstance(capture, dict) or set(capture) != TOP_KEYS or capture.get("schema_version") != 2:
        raise CaptureError("capture schema or fields invalid")
    if not isinstance(allowlist, dict):
        raise CaptureError("allowlist must be an object")
    source = capture["source"]
    if not isinstance(source, dict) or set(source) != SOURCE_KEYS:
        raise CaptureError("source fields invalid")
    kind = _text(source["kind"], "source kind", 32)
    if kind not in SOURCE_HOSTS:
        raise CaptureError("unsupported source kind")
    if source["read_only"] is not True:
        raise CaptureError("capture must be read_only=true")
    method = _text(source["capture_method"], "capture method", 64)
    if method not in SAFE_METHODS or method not in SOURCE_METHODS[kind]:
        raise CaptureError("capture method invalid for source kind")
    source_id = _text(source["id"], "source id", 200)
    title = _text(source["title"], "source title", 500)
    url = _text(source["url"], "source URL", 2000)
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.hostname not in SOURCE_HOSTS[kind]:
        raise CaptureError("source URL outside host allowlist")
    updated = _timestamp(source["updated_at"], "source updated_at")
    captured = _timestamp(source["captured_at"], "source captured_at")
    version = _text(source["version"], "source version", 100)
    _validate_allowlist(source, allowlist)

    blocks = capture["blocks"]
    if not isinstance(blocks, list) or not blocks or len(blocks) > 10000:
        raise CaptureError("blocks must be a non-empty bounded list")
    rendered_blocks = [_render_block(block) for block in blocks]

    revisions = capture["revisions"]
    if not isinstance(revisions, list) or len(revisions) > 10000:
        raise CaptureError("revisions must be a bounded list")
    revision_lines: list[str] = []
    for revision in revisions:
        if not isinstance(revision, dict) or set(revision) != {"version", "updated_at", "author_ref", "message"}:
            raise CaptureError("revision fields invalid")
        revision_lines.append(
            f"- version `{_text(revision['version'], 'revision version', 100)}` "
            f"at `{_timestamp(revision['updated_at'], 'revision updated_at')}` "
            f"by `{_text(revision['author_ref'], 'revision author_ref', 500)}`: "
            f"{_text(revision['message'], 'revision message', 5000)}"
        )

    claims = capture["claims"]
    if not isinstance(claims, list) or len(claims) > 10000:
        raise CaptureError("claims must be a bounded list")
    claim_lines: list[str] = []
    for claim in claims:
        if not isinstance(claim, dict) or set(claim) != {
            "evidence_class",
            "claim",
            "source_ref",
            "observed_at",
            "artifact_sha256",
        }:
            raise CaptureError("claim fields invalid")
        evidence_class = claim["evidence_class"]
        if evidence_class not in EVIDENCE_CLASSES:
            raise CaptureError("unsupported evidence_class")
        observed_at = _timestamp(claim["observed_at"], "claim observed_at")
        artifact_sha256 = claim["artifact_sha256"]
        if not isinstance(artifact_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", artifact_sha256):
            raise CaptureError("claim artifact_sha256 invalid")
        claim_lines.extend(
            [
                f"- evidence_class: `{evidence_class}`",
                f"  - claim: {_text(claim['claim'], 'claim', 20000)}",
                f"  - source_ref: `{_text(claim['source_ref'], 'source_ref', 500)}`",
                f"  - observed_at: `{observed_at}`",
                f"  - artifact_sha256: `{artifact_sha256}`",
            ]
        )

    conflicts = _string_list(capture["conflicts"], "conflicts")
    unresolved = _string_list(capture["unresolved"], "unresolved")
    merge_targets = _string_list(capture["merge_targets"], "merge_targets", maximum=100)
    allowed_targets = allowlist.get("merge_targets")
    if not isinstance(allowed_targets, list) or any(target not in allowed_targets for target in merge_targets):
        raise CaptureError("merge target outside allowlist")

    body = "\n".join(
        [
            "## [SOURCE]",
            f"- source kind: `{kind}`",
            f"- source ID: `{source_id}`",
            f"- title: {title}",
            f"- URL: {url}",
            f"- version: `{version}`",
            f"- updated at: `{updated}`",
            f"- captured at: `{captured}`",
            "- capture mode: `read-only`",
            f"- capture method: `{method}`",
            "",
            "## [CONTENT]",
            *rendered_blocks,
            "",
            "### Revision lineage",
            *(revision_lines or ["- revision history unavailable"]),
            "",
            "### Evidence-class claims",
            *(claim_lines or ["- classified claims unavailable"]),
            "",
            "## [CONFLICT]",
            *([f"- {item}" for item in conflicts] or ["- 확인된 충돌 없음"]),
            "",
            "## [UNRESOLVED]",
            *([f"- {item}" for item in unresolved] or ["- 확인된 미해결 없음"]),
            "",
            "## [HERMES-MERGE]",
            *([f"- {item}" for item in merge_targets] or ["- 자동 병합 대상 없음"]),
            "",
            "## [EVIDENCE]",
            f"- capture method: `{method}`",
            f"- block count: `{len(blocks)}`",
            f"- revision count: `{len(revisions)}`",
            f"- claim count: `{len(claims)}`",
            f"- credential scrub markers: `{json.dumps(capture, ensure_ascii=False).count('[REDACTED]')}`",
            "- promotion status: `HOLD_HUMAN_REVIEW`",
            "",
        ]
    )
    for pattern in SECRET_PATTERNS:
        if pattern.search(body):
            raise CaptureError("secret-looking value found; redact before packet build")
    return CompiledCapture(
        body=body,
        packet_kwargs={
            "source_kind": kind,
            "source_id": source_id,
            "source_title": title,
            "source_url": url,
            "source_version": version,
            "source_updated_at": updated,
            "captured_at": captured,
            "status": "PASS",
            "redaction_count": body.count("[REDACTED]"),
        },
    )


def collect_to_outbox(
    capture: object,
    allowlist: object,
    output_root: Path | str,
    *,
    packet_module=None,
) -> dict[str, object]:
    """Compile one capture and append exact packets to the existing Claude outbox."""
    if packet_module is None:
        import company_knowledge_packet as packet_module  # type: ignore[no-redef]
    compiled = compile_capture(capture, allowlist)
    texts = packet_module.build_packet_texts(compiled.body, **compiled.packet_kwargs)
    paths = packet_module.write_outbox_packets(
        texts,
        output_root,
        timestamp=str(compiled.packet_kwargs["captured_at"]),
    )
    group = packet_module.validate_group([packet_module.parse_packet(text) for text in texts])
    return {
        "status": "PASS",
        "group_id": group.manifest["group_id"],
        "parts": len(paths),
        "bytes": group.manifest["group_bytes"],
        "sha256": group.manifest["group_sha256"],
        "outbox_files": [path.name for path in paths],
        "promotion": "HOLD_HUMAN_REVIEW",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--allowlist", type=Path, required=True)
    parser.add_argument(
        "--outbox",
        type=Path,
        default=Path.home() / ".claude/hermes/outbox/local-claude",
    )
    parser.add_argument("--body-output", type=Path)
    args = parser.parse_args()
    try:
        capture = json.loads(args.capture.read_text(encoding="utf-8", errors="strict"))
        allowlist = json.loads(args.allowlist.read_text(encoding="utf-8", errors="strict"))
        compiled = compile_capture(capture, allowlist)
        if args.body_output is not None:
            args.body_output.write_text(compiled.body, encoding="utf-8", newline="\n")
        result = collect_to_outbox(capture, allowlist, args.outbox)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (CaptureError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"HOLD {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
