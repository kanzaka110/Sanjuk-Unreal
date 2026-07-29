#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
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
stager = load("company_knowledge_case_stager")

BODY = """## [SOURCE]
- source kind: `confluence`
- source ID: `1608679894`
- title: MotionMatching ABP Chooser
- URL: https://shiftupcorp.atlassian.net/wiki/spaces/SB2/pages/1608679894/example
- version: `8`
- updated at: `2026-05-29T10:35:04+09:00`
- captured at: `2026-07-29T09:00:00+09:00`
- capture mode: `read-only`

## [CONTENT]
### 원문
표와 코드 원문이다.

## [CONFLICT]
- 현재 에셋과 충돌 가능

## [UNRESOLVED]
- current measurement 필요

## [HERMES-MERGE]
- 03_Stop과 락온 반전 케이스.md
- 08_원본 커버리지.md

## [EVIDENCE]
- promotion status: `HOLD_HUMAN_REVIEW`
"""


class CaseStagerTests(unittest.TestCase):
    def make_group(self, root: Path) -> Path:
        texts = packet.build_packet_texts(
            BODY,
            source_kind="confluence",
            source_id="1608679894",
            source_title="MotionMatching ABP Chooser",
            source_url="https://shiftupcorp.atlassian.net/wiki/spaces/SB2/pages/1608679894/example",
            source_version="8",
            source_updated_at="2026-05-29T10:35:04+09:00",
            captured_at="2026-07-29T09:00:00+09:00",
        )
        group = packet.validate_group([packet.parse_packet(text) for text in texts])
        store = packet.PacketStore(root / "store")
        self.assertEqual(store.persist(group), "new")
        return store.root / str(group.manifest["group_id"])

    def test_valid_group_creates_deterministic_review_staging_without_promotion(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            group_dir = self.make_group(root)
            result = stager.stage_group(group_dir, root / "staging", packet_module=packet)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["promotion"], "HOLD_HUMAN_REVIEW")
            stage_dir = root / "staging" / result["group_id"]
            note = (stage_dir / "STAGING.md").read_text(encoding="utf-8")
            manifest = json.loads((stage_dir / "MANIFEST.json").read_text(encoding="utf-8"))
            self.assertIn("검토 전 운영 truth로 사용 금지", note)
            self.assertIn("03_Stop과 락온 반전 케이스.md", note)
            self.assertIn(BODY, note)
            self.assertEqual(manifest["promotion"], "HOLD_HUMAN_REVIEW")
            self.assertEqual(set(path.name for path in stage_dir.iterdir()), {"STAGING.md", "MANIFEST.json"})
            self.assertEqual(stager.stage_group(group_dir, root / "staging", packet_module=packet)["result"], "duplicate")


if __name__ == "__main__":
    unittest.main(verbosity=2)
