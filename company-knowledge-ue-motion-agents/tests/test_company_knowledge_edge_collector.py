#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).parent


def load(name: str):
    path = BASE / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


packet = load("company_knowledge_packet")
edge = load("company_knowledge_edge_collector")


ALLOWLIST = {
    "schema_version": 1,
    "confluence": {"spaces": ["SB2"], "page_ids": []},
    "drive": {"folder_ids": []},
    "claude": {"roots": ["H:/내 드라이브/Claude/Sanjuk-Unreal"]},
    "ue": {"asset_roots": ["/Game/Art/Character/PC/PC_01"]},
    "merge_targets": ["03_Stop과 락온 반전 케이스.md", "08_원본 커버리지.md"],
}


CAPTURE = {
    "schema_version": 2,
    "source": {
        "kind": "confluence",
        "id": "1608679894",
        "title": "MotionMatching ABP Chooser",
        "url": "https://shiftupcorp.atlassian.net/wiki/spaces/SB2/pages/1608679894/example",
        "version": "8",
        "updated_at": "2026-05-29T10:35:04+09:00",
        "captured_at": "2026-07-29T09:00:00+09:00",
        "read_only": True,
        "capture_method": "confluence_mcp",
        "scope": {"space": "SB2"},
    },
    "blocks": [
        {"type": "heading", "level": 2, "text": "Stop 분석"},
        {"type": "table", "columns": ["필드", "값"], "rows": [["rrr", "LockOnTarget"]]},
        {"type": "code", "language": "text", "text": "sms=2 rrr=LockOnTarget"},
        {
            "type": "image",
            "attachment_id": "att-1",
            "filename": "frame.png",
            "caption": "정지 직전 프레임",
            "context": "ANIM_REC onset 86건",
        },
    ],
    "revisions": [
        {
            "version": "8",
            "updated_at": "2026-05-29T10:35:04+09:00",
            "author_ref": "account-id-redacted",
            "message": "최종 정리",
        }
    ],
    "claims": [
        {
            "evidence_class": "HISTORICAL_NOTE",
            "claim": "2026-05-29 당시 rrr=LockOnTarget이었다.",
            "source_ref": "row-21",
            "observed_at": "2026-05-29T10:35:04+09:00",
            "artifact_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        },
        {
            "evidence_class": "CURRENT_MEASUREMENT",
            "claim": "현재 CDO 값은 0.2다.",
            "source_ref": "ue-dump-20260729",
            "observed_at": "2026-07-29T08:55:00+09:00",
            "artifact_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        },
    ],
    "conflicts": ["과거 값과 현재 CDO 값을 자동 통합하지 않는다."],
    "unresolved": ["현재 에셋 재실측 교차검증 필요"],
    "merge_targets": ["03_Stop과 락온 반전 케이스.md", "08_원본 커버리지.md"],
}


class EdgeCollectorTests(unittest.TestCase):
    def test_allowed_confluence_capture_round_trips_through_v1_transport(self):
        compiled = edge.compile_capture(CAPTURE, ALLOWLIST)
        self.assertIn("| 필드 | 값 |", compiled.body)
        self.assertIn("```text\nsms=2 rrr=LockOnTarget\n```", compiled.body)
        self.assertIn("attachment_id: `att-1`", compiled.body)
        self.assertIn("evidence_class: `HISTORICAL_NOTE`", compiled.body)
        self.assertIn("evidence_class: `CURRENT_MEASUREMENT`", compiled.body)
        self.assertIn("observed_at: `2026-07-29T08:55:00+09:00`", compiled.body)
        self.assertIn("artifact_sha256: `bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb`", compiled.body)

        texts = packet.build_packet_texts(compiled.body, **compiled.packet_kwargs)
        group = packet.validate_group([packet.parse_packet(text) for text in texts])
        self.assertEqual(group.manifest["source_id"], "1608679894")
        self.assertEqual(group.content.decode("utf-8"), compiled.body)

    def test_source_kind_requires_matching_read_only_capture_method(self):
        changed = copy.deepcopy(CAPTURE)
        changed["source"]["capture_method"] = "drive_readonly"
        with self.assertRaises(edge.CaptureError):
            edge.compile_capture(changed, ALLOWLIST)

    def test_collect_to_outbox_emits_valid_append_only_packets(self):
        with tempfile.TemporaryDirectory() as td:
            result = edge.collect_to_outbox(
                CAPTURE,
                ALLOWLIST,
                Path(td) / "outbox",
                packet_module=packet,
            )
            self.assertEqual(result["status"], "PASS")
            paths = [Path(td) / "outbox" / name for name in result["outbox_files"]]
            group = packet.validate_group(
                [packet.parse_packet(path.read_text(encoding="utf-8")) for path in paths]
            )
            self.assertEqual(group.manifest["group_sha256"], result["sha256"])

    def test_cli_collects_capture_directly_to_outbox(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            capture_path = root / "capture.json"
            allowlist_path = root / "allowlist.json"
            outbox = root / "outbox"
            capture_path.write_text(json.dumps(CAPTURE, ensure_ascii=False), encoding="utf-8")
            allowlist_path.write_text(json.dumps(ALLOWLIST, ensure_ascii=False), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(BASE / "company_knowledge_edge_collector.py"),
                    "--capture",
                    str(capture_path),
                    "--allowlist",
                    str(allowlist_path),
                    "--outbox",
                    str(outbox),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "PASS")
            self.assertEqual(payload["promotion"], "HOLD_HUMAN_REVIEW")
            self.assertTrue(list(outbox.glob("*_CompanyKnowledge.md")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
