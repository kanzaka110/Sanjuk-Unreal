#!/usr/bin/env python3
"""Validate and persist read-only company knowledge Evidence Packets.

The company-side Claude worker owns authenticated source access and emits bounded
Markdown envelopes into the existing GCP Claude outbox. This module never uses
company credentials and never writes to GCP. It validates raw cached envelopes
and persists exact, append-only local artifacts for later Hermes review.
"""
from __future__ import annotations

import argparse
import datetime as dt
try:
    import fcntl
except ImportError:  # Windows company-PC builder path; PacketStore remains Linux-only.
    fcntl = None
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import NamedTuple
from urllib.parse import urlparse

HEADER = "[COMPANY-KNOWLEDGE-PACKET v1]"
CONTENT_BEGIN = "--- CONTENT BEGIN ---\n"
CONTENT_END = "--- CONTENT END ---\n"
MAX_PACKET_BYTES = 64 * 1024
MAX_PART_BYTES = 60 * 1024
MAX_PARTS = 100
MAX_GROUP_BYTES = MAX_PART_BYTES * MAX_PARTS
DEFAULT_RAW_ROOT = Path("/root/.hermes/cache/gcp-claude-outbox")
DEFAULT_STORE_ROOT = Path("/root/.hermes/state/company-knowledge-packets")
ID_RE = re.compile(r"^[a-z][a-z0-9_-]{7,95}$")
PACKET_ID_RE = re.compile(r"^ckp_[a-z0-9_-]{5,87}_p(\d{3})$")
SOURCE_ID_RE = re.compile(r"^[A-Za-z0-9._:/-]{1,200}$")
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
REQUIRED_SECTIONS = (
    "## [SOURCE]",
    "## [CONTENT]",
    "## [CONFLICT]",
    "## [UNRESOLVED]",
    "## [HERMES-MERGE]",
    "## [EVIDENCE]",
)
MANIFEST_KEYS = {
    "schema_version",
    "packet_id",
    "group_id",
    "part_index",
    "part_count",
    "status",
    "source_kind",
    "source_id",
    "source_title",
    "source_url",
    "source_version",
    "source_updated_at",
    "captured_at",
    "read_only",
    "part_bytes",
    "part_sha256",
    "group_bytes",
    "group_sha256",
    "redaction_count",
}
STABLE_GROUP_KEYS = (
    "schema_version",
    "group_id",
    "part_count",
    "status",
    "source_kind",
    "source_id",
    "source_title",
    "source_url",
    "source_version",
    "source_updated_at",
    "captured_at",
    "read_only",
    "group_bytes",
    "group_sha256",
)
ALLOWED_SOURCE_HOSTS = {
    "confluence": {"shiftupcorp.atlassian.net"},
    "drive": {"drive.google.com", "docs.google.com"},
}


class InvalidPacket(ValueError):
    pass


class PacketConflict(RuntimeError):
    pass


class Packet(NamedTuple):
    manifest: dict[str, object]
    content: bytes
    raw: bytes


class PacketGroup(NamedTuple):
    manifest: dict[str, object]
    content: bytes
    parts: tuple[Packet, ...]


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _require_int(value: object, name: str, *, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise InvalidPacket(f"{name} is outside bounds")
    return value


def _require_text(value: object, name: str, *, maximum: int = 500) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise InvalidPacket(f"{name} is invalid")
    return value


def _validate_timestamp(value: object, name: str) -> str:
    text = _require_text(value, name, maximum=64)
    try:
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise InvalidPacket(f"{name} must be ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise InvalidPacket(f"{name} must include timezone")
    return text


def _secret_hits(text: str) -> list[int]:
    return [index for index, pattern in enumerate(SECRET_PATTERNS, 1) if pattern.search(text)]


def _validate_manifest(manifest: object, content: bytes) -> dict[str, object]:
    if not isinstance(manifest, dict) or set(manifest) != MANIFEST_KEYS:
        raise InvalidPacket("manifest has unknown or missing fields")
    if manifest["schema_version"] != 1:
        raise InvalidPacket("unsupported schema_version")
    packet_id = _require_text(manifest["packet_id"], "packet_id", maximum=96)
    group_id = _require_text(manifest["group_id"], "group_id", maximum=96)
    if not ID_RE.fullmatch(group_id):
        raise InvalidPacket("invalid group_id")
    packet_match = PACKET_ID_RE.fullmatch(packet_id)
    if not packet_match:
        raise InvalidPacket("invalid packet_id")
    part_index = _require_int(manifest["part_index"], "part_index", minimum=1, maximum=MAX_PARTS)
    part_count = _require_int(manifest["part_count"], "part_count", minimum=1, maximum=MAX_PARTS)
    if part_index > part_count or int(packet_match.group(1)) != part_index:
        raise InvalidPacket("packet_id or part_index mismatch")
    if manifest["status"] not in {"PASS", "HOLD"}:
        raise InvalidPacket("invalid status")
    source_kind = _require_text(manifest["source_kind"], "source_kind", maximum=32)
    if source_kind not in ALLOWED_SOURCE_HOSTS:
        raise InvalidPacket("unsupported source_kind")
    source_id = _require_text(manifest["source_id"], "source_id", maximum=200)
    if not SOURCE_ID_RE.fullmatch(source_id):
        raise InvalidPacket("invalid source_id")
    _require_text(manifest["source_title"], "source_title", maximum=500)
    source_url = _require_text(manifest["source_url"], "source_url", maximum=2000)
    parsed_url = urlparse(source_url)
    if (
        parsed_url.scheme != "https"
        or parsed_url.username is not None
        or parsed_url.password is not None
        or parsed_url.hostname not in ALLOWED_SOURCE_HOSTS[source_kind]
    ):
        raise InvalidPacket("source_url is outside allowlist")
    _require_text(manifest["source_version"], "source_version", maximum=100)
    _validate_timestamp(manifest["source_updated_at"], "source_updated_at")
    _validate_timestamp(manifest["captured_at"], "captured_at")
    if manifest["read_only"] is not True:
        raise InvalidPacket("capture must be read_only=true")
    part_bytes = _require_int(manifest["part_bytes"], "part_bytes", minimum=1, maximum=MAX_PART_BYTES)
    group_bytes = _require_int(manifest["group_bytes"], "group_bytes", minimum=1, maximum=MAX_GROUP_BYTES)
    _require_int(manifest["redaction_count"], "redaction_count", minimum=0, maximum=1_000_000)
    part_sha = _require_text(manifest["part_sha256"], "part_sha256", maximum=64)
    group_sha = _require_text(manifest["group_sha256"], "group_sha256", maximum=64)
    if not re.fullmatch(r"[0-9a-f]{64}", part_sha) or not re.fullmatch(r"[0-9a-f]{64}", group_sha):
        raise InvalidPacket("digest must be lowercase SHA-256")
    if len(content) != part_bytes or _sha256(content) != part_sha:
        raise InvalidPacket("part bytes or digest mismatch")
    if group_bytes < part_bytes:
        raise InvalidPacket("group_bytes smaller than part")
    return dict(manifest)


def build_packet_texts(
    body: str,
    *,
    source_kind: str,
    source_id: str,
    source_title: str,
    source_url: str,
    source_version: str,
    source_updated_at: str,
    captured_at: str,
    group_id: str | None = None,
    status: str = "PASS",
    redaction_count: int | None = None,
    max_part_bytes: int = 56 * 1024,
) -> list[str]:
    """Build byte-preserving packet envelopes from one canonical Markdown body."""
    if not isinstance(body, str) or not body:
        raise InvalidPacket("source body is empty")
    if type(max_part_bytes) is not int or not 64 <= max_part_bytes <= MAX_PART_BYTES:
        raise InvalidPacket("max_part_bytes is outside builder bounds")
    group_raw = body.encode("utf-8")
    if len(group_raw) > MAX_GROUP_BYTES:
        raise InvalidPacket("source body exceeds group byte cap")
    chunks: list[bytes] = []
    current = bytearray()
    for character in body:
        encoded = character.encode("utf-8")
        if current and len(current) + len(encoded) > max_part_bytes:
            chunks.append(bytes(current))
            current.clear()
        current.extend(encoded)
    if current:
        chunks.append(bytes(current))
    if not chunks or len(chunks) > MAX_PARTS:
        raise InvalidPacket("builder produced invalid part count")
    captured = _validate_timestamp(captured_at, "captured_at")
    _validate_timestamp(source_updated_at, "source_updated_at")
    if group_id is None:
        date = dt.datetime.fromisoformat(captured.replace("Z", "+00:00")).strftime("%Y%m%d")
        source_slug = re.sub(r"[^a-z0-9]+", "_", source_id.lower()).strip("_")[:28] or "source"
        group_id = f"ckg_{date}_{source_kind}_{source_slug}_{_sha256(group_raw)[:12]}"
    if not ID_RE.fullmatch(group_id) or len(group_id) > 87:
        raise InvalidPacket("builder group_id is invalid or too long")
    packet_base = "ckp_" + group_id.removeprefix("ckg_")
    group_sha = _sha256(group_raw)
    total_redactions = body.count("[REDACTED]") if redaction_count is None else redaction_count
    _require_int(total_redactions, "redaction_count", minimum=0, maximum=1_000_000)
    texts: list[str] = []
    for index, chunk in enumerate(chunks, 1):
        manifest = {
            "schema_version": 1,
            "packet_id": f"{packet_base}_p{index:03d}",
            "group_id": group_id,
            "part_index": index,
            "part_count": len(chunks),
            "status": status,
            "source_kind": source_kind,
            "source_id": source_id,
            "source_title": source_title,
            "source_url": source_url,
            "source_version": source_version,
            "source_updated_at": source_updated_at,
            "captured_at": captured,
            "read_only": True,
            "part_bytes": len(chunk),
            "part_sha256": _sha256(chunk),
            "group_bytes": len(group_raw),
            "group_sha256": group_sha,
            "redaction_count": total_redactions if index == 1 else 0,
        }
        text = (
            HEADER
            + "\nmanifest: "
            + json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
            + CONTENT_BEGIN
            + chunk.decode("utf-8")
            + CONTENT_END
        )
        if len(text.encode("utf-8")) > MAX_PACKET_BYTES:
            raise InvalidPacket("built packet exceeds outbox file cap")
        texts.append(text)
    validate_group([parse_packet(text) for text in texts])
    return texts


def write_outbox_packets(
    texts: list[str],
    output_root: Path | str,
    *,
    timestamp: str,
    context: str = "CompanyKnowledge",
) -> list[Path]:
    """Append exact packets to the existing Claude outbox filename contract."""
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,64}", context):
        raise PacketConflict("unsafe outbox context")
    captured = dt.datetime.fromisoformat(_validate_timestamp(timestamp, "timestamp").replace("Z", "+00:00"))
    root = Path(output_root)
    if root.exists():
        if root.is_symlink() or not root.is_dir():
            raise PacketConflict("unsafe outbox root")
    else:
        root.mkdir(parents=True, mode=0o700)
    paths = [
        root / f"{(captured + dt.timedelta(seconds=index)).strftime('%Y-%m-%d_%H%M%S')}_{context}.md"
        for index in range(len(texts))
    ]
    if len(set(paths)) != len(paths):
        raise PacketConflict("outbox filename collision")
    raw_texts = [text.encode("utf-8") for text in texts]
    for path, raw in zip(paths, raw_texts):
        if path.exists() or path.is_symlink():
            if path.is_file() and not path.is_symlink() and path.read_bytes() == raw:
                continue
            raise PacketConflict(f"outbox path conflict: {path.name}")
        _write_exclusive(path, raw)
    for path, raw in zip(paths, raw_texts):
        if path.read_bytes() != raw:
            raise PacketConflict(f"outbox read-back mismatch: {path.name}")
        os.chmod(path, 0o600)
    return paths


def parse_packet(text: str) -> Packet:
    if not isinstance(text, str):
        raise InvalidPacket("packet must be text")
    raw = text.encode("utf-8")
    if not raw or len(raw) > MAX_PACKET_BYTES:
        raise InvalidPacket("packet file is outside byte bounds")
    if CONTROL_RE.search(text):
        raise InvalidPacket("packet contains control characters")
    if _secret_hits(text):
        raise InvalidPacket("secret-looking value found; redact before transport")
    prefix = HEADER + "\nmanifest: "
    if not text.startswith(prefix):
        raise InvalidPacket("missing exact packet header")
    after_prefix = text[len(prefix):]
    manifest_line, separator, payload = after_prefix.partition("\n" + CONTENT_BEGIN)
    if not separator or not manifest_line or "\n" in manifest_line:
        raise InvalidPacket("manifest line or content delimiter is malformed")
    if not payload.endswith(CONTENT_END):
        raise InvalidPacket("missing exact content end delimiter")
    content_text = payload[:-len(CONTENT_END)]
    if CONTENT_BEGIN in content_text or CONTENT_END in content_text:
        raise InvalidPacket("content contains reserved delimiter")
    try:
        manifest_raw = json.loads(manifest_line)
    except json.JSONDecodeError as exc:
        raise InvalidPacket("manifest is not valid JSON") from exc
    content = content_text.encode("utf-8")
    manifest = _validate_manifest(manifest_raw, content)
    return Packet(manifest, content, raw)


def validate_group(packets: list[Packet]) -> PacketGroup:
    if not packets:
        raise InvalidPacket("group has no packets")
    group_ids = {str(packet.manifest["group_id"]) for packet in packets}
    if len(group_ids) != 1:
        raise InvalidPacket("multiple group_ids supplied")
    part_count = int(packets[0].manifest["part_count"])
    if len(packets) != part_count:
        raise InvalidPacket("group is incomplete")
    by_index: dict[int, Packet] = {}
    packet_ids: set[str] = set()
    first = packets[0].manifest
    for packet in packets:
        manifest = packet.manifest
        for key in STABLE_GROUP_KEYS:
            if manifest[key] != first[key]:
                raise InvalidPacket(f"cross-part metadata mismatch: {key}")
        index = int(manifest["part_index"])
        packet_id = str(manifest["packet_id"])
        if index in by_index or packet_id in packet_ids:
            raise InvalidPacket("duplicate part_index or packet_id")
        by_index[index] = packet
        packet_ids.add(packet_id)
    if set(by_index) != set(range(1, part_count + 1)):
        raise InvalidPacket("part index sequence is incomplete")
    ordered = tuple(by_index[index] for index in range(1, part_count + 1))
    content = b"".join(packet.content for packet in ordered)
    if len(content) != first["group_bytes"] or _sha256(content) != first["group_sha256"]:
        raise InvalidPacket("group bytes or digest mismatch")
    try:
        decoded = content.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise InvalidPacket("assembled group is not UTF-8") from exc
    positions: list[int] = []
    for heading in REQUIRED_SECTIONS:
        if decoded.count(heading) != 1:
            raise InvalidPacket(f"required section count invalid: {heading}")
        positions.append(decoded.index(heading))
    if not decoded.startswith(REQUIRED_SECTIONS[0] + "\n") or positions != sorted(positions):
        raise InvalidPacket("required sections are out of order")
    manifest = {key: first[key] for key in STABLE_GROUP_KEYS}
    manifest["packet_count"] = len(ordered)
    manifest["redaction_count"] = sum(int(packet.manifest["redaction_count"]) for packet in ordered)
    manifest["parts"] = [
        {
            "packet_id": packet.manifest["packet_id"],
            "part_index": packet.manifest["part_index"],
            "bytes": packet.manifest["part_bytes"],
            "sha256": packet.manifest["part_sha256"],
        }
        for packet in ordered
    ]
    return PacketGroup(manifest, content, ordered)


def _write_exclusive(path: Path, raw: bytes) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb", closefd=False) as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        os.close(fd)
    os.chmod(path, 0o600)


class PacketStore:
    def __init__(self, root: Path | str):
        self.root = Path(root)
        self.root.mkdir(parents=True, mode=0o700, exist_ok=True)
        if self.root.is_symlink() or not self.root.is_dir():
            raise PacketConflict("unsafe store root")
        os.chmod(self.root, 0o700)
        self.lock_path = self.root / ".lock"

    def _expected(self, group: PacketGroup) -> dict[str, bytes]:
        manifest_raw = (
            json.dumps(group.manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        ).encode("utf-8")
        expected = {"MANIFEST.json": manifest_raw, "GROUP.md": group.content}
        for packet in group.parts:
            index = int(packet.manifest["part_index"])
            expected[f"part-{index:03d}.packet.md"] = packet.raw
        return expected

    @staticmethod
    def _matches(dest: Path, expected: dict[str, bytes]) -> bool:
        if dest.is_symlink() or not dest.is_dir():
            return False
        actual: set[str] = set()
        for path in dest.iterdir():
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode) or info.st_nlink != 1:
                return False
            actual.add(path.name)
        if actual != set(expected):
            return False
        return all((dest / name).read_bytes() == raw for name, raw in expected.items())

    def persist(self, group: PacketGroup) -> str:
        if fcntl is None:
            raise PacketConflict("PacketStore requires POSIX file locking")
        group_id = str(group.manifest["group_id"])
        if not ID_RE.fullmatch(group_id):
            raise PacketConflict("unsafe group_id")
        expected = self._expected(group)
        lock_fd = os.open(self.lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
            dest = self.root / group_id
            if dest.exists() or dest.is_symlink():
                if self._matches(dest, expected):
                    return "duplicate"
                raise PacketConflict("same group_id has different immutable content")
            stage = Path(tempfile.mkdtemp(prefix=f".{group_id}-", dir=self.root))
            os.chmod(stage, 0o700)
            try:
                for name, raw in expected.items():
                    _write_exclusive(stage / name, raw)
                os.replace(stage, dest)
                stage = None
                if not self._matches(dest, expected):
                    raise PacketConflict("post-persist read-back mismatch")
            finally:
                if stage is not None and stage.exists():
                    shutil.rmtree(stage)
            return "new"
        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            os.close(lock_fd)


def import_from_raw_cache(raw_root: Path | str, store: PacketStore) -> dict[str, int]:
    root = Path(raw_root)
    if root.is_symlink() or not root.is_dir():
        raise InvalidPacket("raw cache root is unsafe or missing")
    grouped: dict[str, list[Packet]] = defaultdict(list)
    packet_files = 0
    for path in sorted(root.iterdir(), key=lambda item: item.name):
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise InvalidPacket(f"unsafe raw cache entry: {path.name}")
        if info.st_size > MAX_PACKET_BYTES:
            continue
        raw = path.read_bytes()
        if not raw.startswith((HEADER + "\n").encode("utf-8")):
            continue
        try:
            text = raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise InvalidPacket(f"packet is not UTF-8: {path.name}") from exc
        parsed = parse_packet(text)
        grouped[str(parsed.manifest["group_id"])].append(parsed)
        packet_files += 1
    counts = {"new": 0, "duplicate": 0, "groups": len(grouped), "packet_files": packet_files}
    for group_id in sorted(grouped):
        result = store.persist(validate_group(grouped[group_id]))
        counts[result] += 1
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("files", nargs="+", type=Path)
    importer = sub.add_parser("import")
    importer.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    importer.add_argument("--store", type=Path, default=DEFAULT_STORE_ROOT)
    builder = sub.add_parser("build")
    builder.add_argument("--input", type=Path, required=True)
    builder.add_argument(
        "--outbox",
        type=Path,
        default=Path.home() / ".claude/hermes/outbox/local-claude",
    )
    builder.add_argument("--source-kind", choices=sorted(ALLOWED_SOURCE_HOSTS), required=True)
    builder.add_argument("--source-id", required=True)
    builder.add_argument("--source-title", required=True)
    builder.add_argument("--source-url", required=True)
    builder.add_argument("--source-version", required=True)
    builder.add_argument("--source-updated-at", required=True)
    builder.add_argument("--captured-at")
    builder.add_argument("--group-id")
    builder.add_argument("--status", choices=("PASS", "HOLD"), default="PASS")
    builder.add_argument("--max-part-bytes", type=int, default=56 * 1024)
    args = parser.parse_args()
    try:
        if args.command == "validate":
            packets = [parse_packet(path.read_text(encoding="utf-8", errors="strict")) for path in args.files]
            group = validate_group(packets)
            result = {
                "status": "PASS",
                "group_id": group.manifest["group_id"],
                "parts": group.manifest["packet_count"],
                "bytes": group.manifest["group_bytes"],
                "sha256": group.manifest["group_sha256"],
            }
        elif args.command == "build":
            captured_at = args.captured_at or dt.datetime.now().astimezone().isoformat(timespec="seconds")
            body = args.input.read_text(encoding="utf-8", errors="strict")
            texts = build_packet_texts(
                body,
                group_id=args.group_id,
                source_kind=args.source_kind,
                source_id=args.source_id,
                source_title=args.source_title,
                source_url=args.source_url,
                source_version=args.source_version,
                source_updated_at=args.source_updated_at,
                captured_at=captured_at,
                status=args.status,
                max_part_bytes=args.max_part_bytes,
            )
            paths = write_outbox_packets(texts, args.outbox, timestamp=captured_at)
            built = validate_group([parse_packet(text) for text in texts])
            result = {
                "status": "PASS",
                "group_id": built.manifest["group_id"],
                "parts": len(paths),
                "bytes": built.manifest["group_bytes"],
                "sha256": built.manifest["group_sha256"],
                "outbox_files": [path.name for path in paths],
            }
        else:
            result = import_from_raw_cache(args.raw_root, PacketStore(args.store))
            result["status"] = "PASS"
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (InvalidPacket, PacketConflict, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"HOLD {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
