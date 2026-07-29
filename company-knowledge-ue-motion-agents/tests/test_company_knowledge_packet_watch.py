#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
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
watch = load("company_knowledge_packet_watch")

BODY = """## [SOURCE]
- page: sample

## [CONTENT]
본문

## [CONFLICT]
- 없음

## [UNRESOLVED]
- 없음

## [HERMES-MERGE]
- 08_원본 커버리지.md

## [EVIDENCE]
- sample
"""


class WatchTests(unittest.TestCase):
    def test_new_group_reports_once_and_healthy_duplicate_is_silent(self):
        texts = packet.build_packet_texts(
            BODY,
            source_kind="confluence",
            source_id="1608679894",
            source_title="sample",
            source_url="https://shiftupcorp.atlassian.net/wiki/spaces/SB2/pages/1608679894/sample",
            source_version="1",
            source_updated_at="2026-07-27T16:20:00+09:00",
            captured_at="2026-07-27T22:30:00+09:00",
            max_part_bytes=100,
        )
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "raw"
            store = Path(td) / "store"
            staging = Path(td) / "staging"
            packet.write_outbox_packets(texts, raw, timestamp="2026-07-27T22:30:00+09:00")
            first = watch.run_once(raw, store, staging)
            second = watch.run_once(raw, store, staging)
            self.assertIn("PASS", first)
            self.assertIn("new=1", first)
            self.assertTrue(list(staging.glob("*/STAGING.md")))
            self.assertEqual(second, "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
