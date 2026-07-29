#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("company_knowledge_packet.py")
spec = importlib.util.spec_from_file_location("company_knowledge_packet", MODULE_PATH)
packet = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(packet)


REQUIRED_BODY = """## [SOURCE]
- page: MotionMatching / ABP / Chooser

## [CONTENT]
### Chooser
원문 본문이다.

## [CONFLICT]
- 없음

## [UNRESOLVED]
- 현재 UE 에셋 재실측 필요

## [HERMES-MERGE]
- 01_초우저 평가와 변수 수명.md

## [EVIDENCE]
- Confluence page ID 1608679894, version 42
"""


def make_parts(body: str = REQUIRED_BODY, *, group_id: str = "ckg_20260727_motionmatching", part_count: int = 2):
    raw = body.encode("utf-8")
    cuts = [len(body) * i // part_count for i in range(part_count + 1)]
    chunks = [body[cuts[i]:cuts[i + 1]].encode("utf-8") for i in range(part_count)]
    group_sha = hashlib.sha256(raw).hexdigest()
    parts = []
    for index, chunk in enumerate(chunks, 1):
        manifest = {
            "schema_version": 1,
            "packet_id": f"ckp_20260727_motionmatching_p{index:03d}",
            "group_id": group_id,
            "part_index": index,
            "part_count": part_count,
            "status": "PASS",
            "source_kind": "confluence",
            "source_id": "1608679894",
            "source_title": "MotionMatching / ABP / Chooser",
            "source_url": "https://shiftupcorp.atlassian.net/wiki/spaces/SB2/pages/1608679894/example",
            "source_version": "42",
            "source_updated_at": "2026-07-27T16:20:00+09:00",
            "captured_at": "2026-07-27T22:30:00+09:00",
            "read_only": True,
            "part_bytes": len(chunk),
            "part_sha256": hashlib.sha256(chunk).hexdigest(),
            "group_bytes": len(raw),
            "group_sha256": group_sha,
            "redaction_count": 0,
        }
        text = (
            "[COMPANY-KNOWLEDGE-PACKET v1]\n"
            + "manifest: "
            + json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n--- CONTENT BEGIN ---\n"
            + chunk.decode("utf-8")
            + "--- CONTENT END ---\n"
        )
        parts.append(text)
    return parts


class ParsingTests(unittest.TestCase):
    def test_parses_valid_part_and_verifies_digest(self):
        parsed = packet.parse_packet(make_parts(part_count=1)[0])
        self.assertEqual(parsed.manifest["source_id"], "1608679894")
        self.assertEqual(parsed.content.decode("utf-8"), REQUIRED_BODY)

    def test_rejects_digest_tamper_and_secret_pattern(self):
        valid = make_parts(part_count=1)[0]
        with self.assertRaises(packet.InvalidPacket):
            packet.parse_packet(valid.replace("원문 본문이다.", "변조된 본문이다."))
        secret_body = REQUIRED_BODY.replace("원문 본문이다.", "token=xoxb-12345678901234567890")
        with self.assertRaises(packet.InvalidPacket):
            packet.parse_packet(make_parts(secret_body, part_count=1)[0])

    def test_rejects_unknown_manifest_field_and_non_read_only_capture(self):
        valid = make_parts(part_count=1)[0]
        line = valid.splitlines()[1]
        manifest = json.loads(line.removeprefix("manifest: "))
        manifest["surprise"] = "value"
        bad = valid.replace(line, "manifest: " + json.dumps(manifest, separators=(",", ":")))
        with self.assertRaises(packet.InvalidPacket):
            packet.parse_packet(bad)
        manifest.pop("surprise")
        manifest["read_only"] = False
        bad = valid.replace(line, "manifest: " + json.dumps(manifest, separators=(",", ":")))
        with self.assertRaises(packet.InvalidPacket):
            packet.parse_packet(bad)


class BuilderTests(unittest.TestCase):
    def test_builder_round_trips_large_utf8_body_through_multiple_parts(self):
        body = REQUIRED_BODY.replace("원문 본문이다.", "한글 원문과 code `x = 1`이다.\n" * 30)
        texts = packet.build_packet_texts(
            body,
            group_id="ckg_20260727_motionmatching",
            source_kind="confluence",
            source_id="1608679894",
            source_title="MotionMatching / ABP / Chooser",
            source_url="https://shiftupcorp.atlassian.net/wiki/spaces/SB2/pages/1608679894/example",
            source_version="42",
            source_updated_at="2026-07-27T16:20:00+09:00",
            captured_at="2026-07-27T22:30:00+09:00",
            max_part_bytes=220,
        )
        self.assertGreater(len(texts), 1)
        group = packet.validate_group([packet.parse_packet(text) for text in texts])
        self.assertEqual(group.content.decode("utf-8"), body)
        self.assertTrue(all(len(text.encode("utf-8")) <= packet.MAX_PACKET_BYTES for text in texts))

    def test_outbox_writer_is_append_only(self):
        texts = packet.build_packet_texts(
            REQUIRED_BODY,
            group_id="ckg_20260727_motionmatching",
            source_kind="confluence",
            source_id="1608679894",
            source_title="MotionMatching / ABP / Chooser",
            source_url="https://shiftupcorp.atlassian.net/wiki/spaces/SB2/pages/1608679894/example",
            source_version="42",
            source_updated_at="2026-07-27T16:20:00+09:00",
            captured_at="2026-07-27T22:30:00+09:00",
            max_part_bytes=220,
        )
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "outbox"
            written = packet.write_outbox_packets(
                texts, root, timestamp="2026-07-27T22:30:00+09:00"
            )
            duplicate = packet.write_outbox_packets(
                texts, root, timestamp="2026-07-27T22:30:00+09:00"
            )
            self.assertEqual(written, duplicate)
            self.assertTrue(all(path.name.endswith("_CompanyKnowledge.md") for path in written))
            self.assertTrue(all((os.stat(path).st_mode & 0o777) == 0o600 for path in written))
            changed = list(texts)
            changed[0] += "\n"
            with self.assertRaises(packet.PacketConflict):
                packet.write_outbox_packets(
                    changed, root, timestamp="2026-07-27T22:30:00+09:00"
                )


class GroupTests(unittest.TestCase):
    def test_assembles_complete_group_and_requires_section_order(self):
        parts = [packet.parse_packet(text) for text in make_parts()]
        group = packet.validate_group(list(reversed(parts)))
        self.assertEqual(group.content.decode("utf-8"), REQUIRED_BODY)
        self.assertEqual(group.manifest["part_count"], 2)

        wrong_order = REQUIRED_BODY.replace(
            "## [CONFLICT]\n- 없음\n\n## [UNRESOLVED]",
            "## [UNRESOLVED]\n- 현재 UE 에셋 재실측 필요\n\n## [CONFLICT]",
        )
        with self.assertRaises(packet.InvalidPacket):
            packet.validate_group([packet.parse_packet(make_parts(wrong_order, part_count=1)[0])])

    def test_rejects_missing_part_and_cross_part_metadata_conflict(self):
        texts = make_parts()
        with self.assertRaises(packet.InvalidPacket):
            packet.validate_group([packet.parse_packet(texts[0])])
        second_lines = texts[1].splitlines()
        manifest = json.loads(second_lines[1].removeprefix("manifest: "))
        manifest["source_version"] = "43"
        second_lines[1] = "manifest: " + json.dumps(manifest, separators=(",", ":"))
        with self.assertRaises(packet.InvalidPacket):
            packet.validate_group([
                packet.parse_packet(texts[0]),
                packet.parse_packet("\n".join(second_lines) + "\n"),
            ])


class StoreAndScanTests(unittest.TestCase):
    def test_append_only_store_converges_exact_duplicate_and_blocks_conflict(self):
        group = packet.validate_group([packet.parse_packet(x) for x in make_parts(part_count=1)])
        with tempfile.TemporaryDirectory() as td:
            store = packet.PacketStore(Path(td) / "store")
            self.assertEqual(store.persist(group), "new")
            self.assertEqual(store.persist(group), "duplicate")
            conflict_parts = make_parts(REQUIRED_BODY.replace("원문 본문이다.", "다른 정본이다."), part_count=1)
            conflict = packet.validate_group([packet.parse_packet(conflict_parts[0])])
            with self.assertRaises(packet.PacketConflict):
                store.persist(conflict)
            dest = Path(td) / "store" / group.manifest["group_id"]
            self.assertEqual((dest / "GROUP.md").read_bytes(), group.content)
            self.assertEqual(os.stat(dest).st_mode & 0o777, 0o700)
            self.assertEqual(os.stat(dest / "GROUP.md").st_mode & 0o777, 0o600)

    def test_scan_imports_only_exact_packet_envelopes(self):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "raw"
            store_root = Path(td) / "store"
            raw.mkdir()
            (raw / "2026-07-27_220000_ordinary.md").write_text("[LOCAL-CLAUDE] routine note\n", encoding="utf-8")
            for i, text in enumerate(make_parts(), 1):
                (raw / f"2026-07-27_22000{i}_CompanyKnowledge.md").write_text(text, encoding="utf-8")
            result = packet.import_from_raw_cache(raw, packet.PacketStore(store_root))
            self.assertEqual(result, {"new": 1, "duplicate": 0, "groups": 1, "packet_files": 2})


if __name__ == "__main__":
    unittest.main(verbosity=2)
