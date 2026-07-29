#!/usr/bin/env python3
"""Validate and align UE motion evidence without guessing a verdict.

Runs on the company PC against local read-only evidence. It requires a real
30 fps video, ANIM_REC records, two synchronization anchors, and a current UE
asset dump. The output remains HOLD_HERMES_REVIEW until an AI reviews it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from fractions import Fraction
from pathlib import Path


class MotionEvidenceError(ValueError):
    pass


SHA_RE = re.compile(r"^[0-9a-f]{64}$")
FIELD_RE = re.compile(r'"?([A-Za-z_][A-Za-z0-9_]*)"?=("(?:[^"\\]|\\.)*"|[^,\s]+)')
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
SECRET_RE = re.compile(
    r"(?i)(?:password|passwd|client[_-]?secret|access[_-]?token|refresh[_-]?token|api[_-]?key|authorization)\s*[:=]\s*(?!\[REDACTED\])[^\s,;}]+"
)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _regular_file(path: Path, label: str) -> bytes:
    try:
        info = path.lstat()
    except FileNotFoundError as exc:
        raise MotionEvidenceError(f"missing {label}") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise MotionEvidenceError(f"unsafe {label}")
    return path.read_bytes()


def _finite_text(value: object, label: str, *, limit: int = 4000) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit or CONTROL_RE.search(value):
        raise MotionEvidenceError(f"invalid {label}")
    return value.strip()


def _scan_secrets(value: object) -> None:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True)
    if SECRET_RE.search(raw):
        raise MotionEvidenceError("credential-like content must be [REDACTED]")


def _probe_video(video: Path) -> dict[str, object]:
    try:
        proc = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=avg_frame_rate,r_frame_rate,nb_frames,duration",
                "-of",
                "json",
                str(video),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
            env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LC_ALL": "C", "LANG": "C"},
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise MotionEvidenceError("ffprobe unavailable or timed out") from exc
    if proc.returncode != 0:
        raise MotionEvidenceError("ffprobe rejected video")
    try:
        payload = json.loads(proc.stdout)
        stream = payload["streams"][0]
        fps = float(Fraction(stream["avg_frame_rate"]))
        r_fps = float(Fraction(stream["r_frame_rate"]))
        frame_count = int(stream["nb_frames"])
        duration = float(stream["duration"])
    except (KeyError, IndexError, TypeError, ValueError, ZeroDivisionError, json.JSONDecodeError) as exc:
        raise MotionEvidenceError("ffprobe output incomplete") from exc
    if frame_count <= 0 or duration <= 0:
        raise MotionEvidenceError("video has no usable frames")
    return {
        "method": "ffprobe-readonly",
        "fps": fps,
        "r_fps": r_fps,
        "frame_count": frame_count,
        "duration_s": duration,
    }


def _validate_video(video: Path, manifest: object) -> tuple[dict[str, object], list[dict[str, object]], dict[str, object]]:
    if not isinstance(manifest, dict) or set(manifest) != {
        "schema_version",
        "captured_at",
        "capture_method",
        "bytes",
        "sha256",
        "expected_fps",
        "observations",
    }:
        raise MotionEvidenceError("video manifest fields invalid")
    if manifest["schema_version"] != 1 or manifest["capture_method"] != "screen_recording_readonly":
        raise MotionEvidenceError("video capture contract invalid")
    _finite_text(manifest["captured_at"], "video captured_at", limit=80)
    if manifest["expected_fps"] != 30:
        raise MotionEvidenceError("video expected_fps must be 30")
    raw = _regular_file(video, "video")
    if manifest["bytes"] != len(raw) or manifest["sha256"] != _sha256(raw) or not SHA_RE.fullmatch(str(manifest["sha256"])):
        raise MotionEvidenceError("video integrity mismatch")
    probe = _probe_video(video)
    if abs(float(probe["fps"]) - 30.0) > 0.001 or abs(float(probe["r_fps"]) - 30.0) > 0.001:
        raise MotionEvidenceError("video is not constant 30 fps")
    observations = manifest["observations"]
    if not isinstance(observations, list) or not observations:
        raise MotionEvidenceError("video observations missing")
    normalized: list[dict[str, object]] = []
    seen: set[int] = set()
    for entry in observations:
        if not isinstance(entry, dict) or set(entry) != {"frame", "caption"}:
            raise MotionEvidenceError("video observation fields invalid")
        frame = entry["frame"]
        if not isinstance(frame, int) or isinstance(frame, bool) or frame < 0 or frame >= int(probe["frame_count"]) or frame in seen:
            raise MotionEvidenceError("video observation frame invalid")
        seen.add(frame)
        normalized.append({"frame": frame, "caption": _finite_text(entry["caption"], "video caption", limit=1000)})
    normalized.sort(key=lambda item: int(item["frame"]))
    return manifest, normalized, probe


def _coerce(value: str) -> object:
    if value.startswith('"') and value.endswith('"'):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value[1:-1]
    lower = value.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    if lower in {"none", "null"}:
        return None
    try:
        if re.fullmatch(r"[-+]?\d+", value):
            return int(value)
        if re.fullmatch(r"[-+]?(?:\d+\.\d*|\d*\.\d+)(?:[eE][-+]?\d+)?", value):
            return float(value)
    except ValueError:
        pass
    return value


def _parse_anim_rec(path: Path) -> tuple[list[dict[str, object]], dict[str, object]]:
    raw = _regular_file(path, "ANIM_REC log")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise MotionEvidenceError("ANIM_REC log is not UTF-8") from exc
    records: list[dict[str, object]] = []
    seen: set[int] = set()
    for line in text.splitlines():
        if "[ANIM_REC]" not in line:
            continue
        payload = line.split("[ANIM_REC]", 1)[1]
        payload = re.sub(r"(?<=\d),(?=\d)", "", payload)
        fields = {match.group(1): _coerce(match.group(2)) for match in FIELD_RE.finditer(payload)}
        frame = fields.get("f")
        if not isinstance(frame, int) or isinstance(frame, bool) or frame < 0:
            raise MotionEvidenceError("ANIM_REC record lacks integer f")
        if frame in seen:
            raise MotionEvidenceError("duplicate ANIM_REC frame")
        if "sms" not in fields or "clip" not in fields:
            raise MotionEvidenceError("ANIM_REC record lacks sms or clip")
        seen.add(frame)
        records.append({"frame": frame, "fields": fields})
    records.sort(key=lambda item: int(item["frame"]))
    if len(records) < 2:
        raise MotionEvidenceError("insufficient ANIM_REC records")
    return records, {"bytes": len(raw), "sha256": _sha256(raw), "record_count": len(records)}


def _validate_assets(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {
        "schema_version",
        "captured_at",
        "capture_method",
        "project_revision",
        "chooser_rows",
        "pose_search_databases",
        "animation_blueprint",
    }:
        raise MotionEvidenceError("asset dump fields invalid")
    if value["schema_version"] != 1 or value["capture_method"] != "ue_readonly_dump":
        raise MotionEvidenceError("asset dump is not CURRENT_MEASUREMENT")
    _finite_text(value["captured_at"], "asset captured_at", limit=80)
    _finite_text(value["project_revision"], "project revision", limit=300)
    if not isinstance(value["chooser_rows"], list) or not value["chooser_rows"]:
        raise MotionEvidenceError("chooser row dump missing")
    if not isinstance(value["pose_search_databases"], list) or not value["pose_search_databases"]:
        raise MotionEvidenceError("pose search database dump missing")
    if not isinstance(value["animation_blueprint"], dict) or not value["animation_blueprint"]:
        raise MotionEvidenceError("animation blueprint dump missing")
    return value


def _validate_request(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {
        "schema_version",
        "hypothesis",
        "counterarguments",
        "historical_notes",
        "missing_candidates",
        "single_variable_check",
        "anchors",
    }:
        raise MotionEvidenceError("review request fields invalid")
    if value["schema_version"] != 1:
        raise MotionEvidenceError("review request schema invalid")
    hypothesis = value["hypothesis"]
    if not isinstance(hypothesis, dict) or set(hypothesis) != {"id", "statement"}:
        raise MotionEvidenceError("exactly one hypothesis is required")
    _finite_text(hypothesis["id"], "hypothesis id", limit=100)
    _finite_text(hypothesis["statement"], "hypothesis statement", limit=1000)
    counterarguments = value["counterarguments"]
    if not isinstance(counterarguments, list) or len(counterarguments) > 3:
        raise MotionEvidenceError("counterarguments must be a list of at most 3")
    for item in counterarguments:
        _finite_text(item, "counterargument", limit=1000)
    notes = value["historical_notes"]
    if not isinstance(notes, list):
        raise MotionEvidenceError("historical_notes invalid")
    for note in notes:
        if not isinstance(note, dict) or set(note) != {"claim", "source_ref"}:
            raise MotionEvidenceError("historical note provenance invalid")
        _finite_text(note["claim"], "historical claim", limit=2000)
        _finite_text(note["source_ref"], "historical source_ref", limit=500)
    candidates = value["missing_candidates"]
    if not isinstance(candidates, list):
        raise MotionEvidenceError("missing_candidates invalid")
    for item in candidates:
        _finite_text(item, "missing candidate", limit=1000)
    check = value["single_variable_check"]
    if not isinstance(check, dict) or set(check) != {"variable", "baseline", "candidate"}:
        raise MotionEvidenceError("single variable check invalid")
    _finite_text(check["variable"], "single variable", limit=200)
    anchors = value["anchors"]
    if not isinstance(anchors, list) or len(anchors) != 2:
        raise MotionEvidenceError("exactly two synchronization anchors are required")
    normalized: list[dict[str, int]] = []
    for anchor in anchors:
        if not isinstance(anchor, dict) or set(anchor) != {"video_frame", "anim_frame"}:
            raise MotionEvidenceError("anchor fields invalid")
        video_frame = anchor["video_frame"]
        anim_frame = anchor["anim_frame"]
        if not isinstance(video_frame, int) or isinstance(video_frame, bool) or video_frame < 0:
            raise MotionEvidenceError("anchor video frame invalid")
        if not isinstance(anim_frame, int) or isinstance(anim_frame, bool) or anim_frame < 0:
            raise MotionEvidenceError("anchor ANIM_REC frame invalid")
        normalized.append({"video_frame": video_frame, "anim_frame": anim_frame})
    normalized.sort(key=lambda item: item["video_frame"])
    if normalized[0]["video_frame"] == normalized[1]["video_frame"] or normalized[0]["anim_frame"] == normalized[1]["anim_frame"]:
        raise MotionEvidenceError("anchors do not define a timeline")
    value = dict(value)
    value["anchors"] = normalized
    return value


def _align(
    observations: list[dict[str, object]],
    records: list[dict[str, object]],
    anchors: list[dict[str, int]],
    video_frames: int,
) -> tuple[list[dict[str, object]], dict[str, float]]:
    first, second = anchors
    if second["video_frame"] >= video_frames:
        raise MotionEvidenceError("anchor outside video")
    frames = {int(item["frame"]): item for item in records}
    if first["anim_frame"] not in frames or second["anim_frame"] not in frames:
        raise MotionEvidenceError("anchor outside ANIM_REC")
    slope = (second["anim_frame"] - first["anim_frame"]) / (second["video_frame"] - first["video_frame"])
    if slope <= 0 or slope > 10:
        raise MotionEvidenceError("implausible synchronization slope")
    record_frames = sorted(frames)
    aligned: list[dict[str, object]] = []
    for observation in observations:
        video_frame = int(observation["frame"])
        predicted = first["anim_frame"] + (video_frame - first["video_frame"]) * slope
        nearest = min(record_frames, key=lambda item: (abs(item - predicted), item))
        delta = nearest - predicted
        if abs(delta) > max(1.0, slope / 2.0):
            raise MotionEvidenceError("ANIM_REC coverage gap near observed frame")
        record = frames[nearest]
        aligned.append(
            {
                "video_frame": video_frame,
                "video_time_s": round(video_frame / 30.0, 6),
                "caption": observation["caption"],
                "predicted_anim_frame": round(predicted, 6),
                "anim_frame": nearest,
                "alignment_delta_frames": round(delta, 6),
                "fields": record["fields"],
            }
        )
    return aligned, {"anim_frames_per_video_frame": slope, "video_fps": 30.0}


def _md(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _report(
    aligned: list[dict[str, object]],
    assets: dict[str, object],
    request: dict[str, object],
    provenance: dict[str, object],
) -> str:
    hypothesis = request["hypothesis"]
    lines = [
        f"# UE 모션 증거 검수 staging — {_md(hypothesis['id'])}",
        "",
        "> 정렬 검증만 통과했다. AI 검수 전 결론·운영 truth·에셋 수정으로 승격 금지.",
        "",
        "## 가설",
        f"- {_md(hypothesis['statement'])}",
        "",
        "## 타임라인 정렬 — CURRENT_MEASUREMENT",
        "|영상 프레임|시각(s)|시각 관찰|ANIM_REC f|clip|sms|delta|",
        "|---:|---:|---|---:|---|---|---:|",
    ]
    for row in aligned:
        fields = row["fields"]
        lines.append(
            f"|{row['video_frame']}|{row['video_time_s']}|{_md(row['caption'])}|{row['anim_frame']}|"
            f"{_md(fields.get('clip'))}|{_md(fields.get('sms'))}|{row['alignment_delta_frames']}|"
        )
    lines.extend(["", "## 현재 에셋 실측 — CURRENT_MEASUREMENT", "```json", json.dumps(assets, ensure_ascii=False, sort_keys=True, indent=2), "```", "", "## 반박"])
    counterarguments = request["counterarguments"]
    lines.extend([f"- {_md(item)}" for item in counterarguments] or ["- 없음"])
    lines.extend(["", "## 메모리 충돌", "- 아래는 `HISTORICAL_NOTE`이며 현재 실측보다 자동 승격하지 않는다."])
    notes = request["historical_notes"]
    lines.extend([f"- {_md(item['claim'])} — source_ref=`{_md(item['source_ref'])}`" for item in notes] or ["- 없음"])
    lines.extend(["", "## 빠진 후보"])
    lines.extend([f"- {_md(item)}" for item in request["missing_candidates"]] or ["- 없음"])
    check = request["single_variable_check"]
    lines.extend(
        [
            "",
            "## 단일변수 체크",
            f"- 변수: `{_md(check['variable'])}`",
            f"- 기준값: `{_md(check['baseline'])}`",
            f"- 후보값: `{_md(check['candidate'])}`",
            "- 실제 적용·관찰: 미실행. 회사 PC에서 한 변수만 바꿔 재수집 필요.",
            "",
            "## 종합 판정",
            "- `HOLD_HERMES_REVIEW` — 정렬은 PASS지만 AI 반박·실기기 비교 전 결론 금지.",
            "",
            "## provenance",
            "```json",
            json.dumps(provenance, ensure_ascii=False, sort_keys=True, indent=2),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def build_review_bundle(
    video_path: Path | str,
    video_manifest: object,
    anim_rec_path: Path | str,
    asset_dump: object,
    review_request: object,
) -> dict[str, object]:
    _scan_secrets(video_manifest)
    _scan_secrets(asset_dump)
    _scan_secrets(review_request)
    manifest, observations, probe = _validate_video(Path(video_path), video_manifest)
    records, log_provenance = _parse_anim_rec(Path(anim_rec_path))
    assets = _validate_assets(asset_dump)
    request = _validate_request(review_request)
    aligned, mapping = _align(observations, records, request["anchors"], int(probe["frame_count"]))
    asset_raw = (json.dumps(assets, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    request_raw = (json.dumps(request, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    provenance = {
        "video": {
            "bytes": manifest["bytes"],
            "sha256": manifest["sha256"],
            "captured_at": manifest["captured_at"],
            "probe": probe,
        },
        "anim_rec": log_provenance,
        "asset_dump": {"bytes": len(asset_raw), "sha256": _sha256(asset_raw), "captured_at": assets["captured_at"], "evidence_class": "CURRENT_MEASUREMENT"},
        "review_request": {"bytes": len(request_raw), "sha256": _sha256(request_raw)},
        "mapping": mapping,
    }
    result: dict[str, object] = {
        "schema_version": 1,
        "status": "PASS_ALIGNMENT",
        "verdict": "HOLD_HERMES_REVIEW",
        "aligned": aligned,
        "probe": probe,
        "provenance": provenance,
    }
    result["report"] = _report(aligned, assets, request, provenance)
    _scan_secrets(result)
    return result


def _load_json(path: Path, label: str) -> object:
    raw = _regular_file(path, label)
    try:
        return json.loads(raw.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MotionEvidenceError(f"invalid {label}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--video-manifest", type=Path, required=True)
    parser.add_argument("--anim-rec", type=Path, required=True)
    parser.add_argument("--asset-dump", type=Path, required=True)
    parser.add_argument("--review-request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = build_review_bundle(
            args.video,
            _load_json(args.video_manifest, "video manifest"),
            args.anim_rec,
            _load_json(args.asset_dump, "asset dump"),
            _load_json(args.review_request, "review request"),
        )
        if args.output.exists() or args.output.is_symlink():
            raise MotionEvidenceError("output is append-only")
        args.output.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
        raw = str(result["report"]).encode("utf-8")
        fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            os.write(fd, raw)
            os.fsync(fd)
        finally:
            os.close(fd)
        print(json.dumps({"status": result["status"], "verdict": result["verdict"], "output": str(args.output), "bytes": len(raw), "sha256": _sha256(raw)}, ensure_ascii=False, sort_keys=True))
        return 0
    except (MotionEvidenceError, OSError, ValueError) as exc:
        fingerprint = _sha256(str(exc).encode("utf-8"))[:12]
        print(f"HOLD Motion Evidence: {type(exc).__name__} ({fingerprint})", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
