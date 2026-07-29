#!/usr/bin/env python3
"""Create immutable human-review staging notes from validated company packets.

The stager never edits a target case wiki. It produces a derived review artifact
whose promotion state is always HOLD_HUMAN_REVIEW.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tempfile
from pathlib import Path


class StagingError(ValueError):
    pass


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _load_group(group_dir: Path, packet_module):
    if group_dir.is_symlink() or not group_dir.is_dir():
        raise StagingError("group directory unsafe or missing")
    entries = list(group_dir.iterdir())
    for path in entries:
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise StagingError(f"unsafe group entry: {path.name}")
    part_paths = sorted(group_dir.glob("part-*.packet.md"))
    expected_names = {"MANIFEST.json", "GROUP.md"} | {path.name for path in part_paths}
    if {path.name for path in entries} != expected_names or not part_paths:
        raise StagingError("group file roster invalid")
    packets = [packet_module.parse_packet(path.read_text(encoding="utf-8", errors="strict")) for path in part_paths]
    group = packet_module.validate_group(packets)
    group_id = str(group.manifest["group_id"])
    if group_dir.name != group_id:
        raise StagingError("group path identity mismatch")
    expected_manifest = (json.dumps(group.manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    if (group_dir / "MANIFEST.json").read_bytes() != expected_manifest:
        raise StagingError("stored manifest mismatch")
    if (group_dir / "GROUP.md").read_bytes() != group.content:
        raise StagingError("stored group body mismatch")
    return group


def _extract_merge_targets(body: str) -> list[str]:
    marker = "## [HERMES-MERGE]\n"
    end = "\n## [EVIDENCE]\n"
    if body.count(marker) != 1 or body.count(end) != 1:
        raise StagingError("merge section malformed")
    section = body.split(marker, 1)[1].split(end, 1)[0]
    targets: list[str] = []
    for line in section.splitlines():
        if not line.strip():
            continue
        if not line.startswith("- "):
            raise StagingError("merge target line malformed")
        target = line[2:].strip().strip("`")
        if not target or len(target) > 200 or "/" in target or "\\" in target or target in {".", ".."}:
            raise StagingError("unsafe merge target")
        targets.append(target)
    return targets


def _safe_title(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StagingError("source title missing")
    text = re.sub(r"[\x00-\x1f\x7f/\\\[\]]+", " ", value)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:160] or "회사 지식 Evidence Packet"


def _expected_outputs(group) -> dict[str, bytes]:
    manifest = group.manifest
    body = group.content.decode("utf-8", errors="strict")
    targets = _extract_merge_targets(body)
    title = _safe_title(manifest["source_title"])
    note = "\n".join(
        [
            "---",
            "type: company-knowledge-review-staging",
            f"group_id: {manifest['group_id']}",
            f"source_kind: {manifest['source_kind']}",
            f"source_id: {manifest['source_id']}",
            f"source_version: {manifest['source_version']}",
            f"source_updated_at: {manifest['source_updated_at']}",
            f"captured_at: {manifest['captured_at']}",
            f"group_sha256: {manifest['group_sha256']}",
            "promotion: HOLD_HUMAN_REVIEW",
            "---",
            "",
            f"# {title} — 검토 staging",
            "",
            "> 검토 전 운영 truth로 사용 금지. 기존 케이스 위키를 자동 수정하지 않는다.",
            "",
            "## 제안 병합 대상",
            *([f"- `{target}`" for target in targets] or ["- 없음"]),
            "",
            "## 정본 packet body",
            "",
            body.rstrip("\n"),
            "",
        ]
    ).encode("utf-8")
    stage_manifest = {
        "schema_version": 1,
        "group_id": manifest["group_id"],
        "source_id": manifest["source_id"],
        "source_version": manifest["source_version"],
        "source_updated_at": manifest["source_updated_at"],
        "captured_at": manifest["captured_at"],
        "group_sha256": manifest["group_sha256"],
        "merge_targets": targets,
        "promotion": "HOLD_HUMAN_REVIEW",
        "staging_note": "STAGING.md",
        "staging_note_bytes": len(note),
        "staging_note_sha256": _sha256(note),
    }
    manifest_raw = (json.dumps(stage_manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    return {"STAGING.md": note, "MANIFEST.json": manifest_raw}


def _matches(dest: Path, expected: dict[str, bytes]) -> bool:
    if dest.is_symlink() or not dest.is_dir():
        return False
    entries = list(dest.iterdir())
    if {path.name for path in entries} != set(expected):
        return False
    for path in entries:
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            return False
    return all((dest / name).read_bytes() == raw for name, raw in expected.items())


def stage_group(group_dir: Path | str, staging_root: Path | str, *, packet_module=None) -> dict[str, object]:
    if packet_module is None:
        import company_knowledge_packet as packet_module  # type: ignore[no-redef]
    group = _load_group(Path(group_dir), packet_module)
    root = Path(staging_root)
    if root.exists() and (root.is_symlink() or not root.is_dir()):
        raise StagingError("staging root unsafe")
    root.mkdir(parents=True, mode=0o700, exist_ok=True)
    os.chmod(root, 0o700)
    group_id = str(group.manifest["group_id"])
    dest = root / group_id
    expected = _expected_outputs(group)
    if dest.exists() or dest.is_symlink():
        if _matches(dest, expected):
            result = "duplicate"
        else:
            raise StagingError("immutable staging conflict")
    else:
        stage = Path(tempfile.mkdtemp(prefix=f".{group_id}-", dir=root))
        try:
            os.chmod(stage, 0o700)
            for name, raw in expected.items():
                fd = os.open(stage / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                try:
                    os.write(fd, raw)
                    os.fsync(fd)
                finally:
                    os.close(fd)
            os.replace(stage, dest)
            stage = None
            if not _matches(dest, expected):
                raise StagingError("post-stage read-back mismatch")
            result = "new"
        finally:
            if stage is not None and stage.exists():
                shutil.rmtree(stage)
    return {
        "status": "PASS",
        "result": result,
        "group_id": group_id,
        "promotion": "HOLD_HUMAN_REVIEW",
        "staging_path": str(dest),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("group_dir", type=Path)
    parser.add_argument("--staging-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(stage_group(args.group_dir, args.staging_root), ensure_ascii=False, sort_keys=True))
        return 0
    except (StagingError, OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"HOLD {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
