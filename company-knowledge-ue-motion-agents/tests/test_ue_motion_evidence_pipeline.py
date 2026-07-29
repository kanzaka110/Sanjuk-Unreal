#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
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


motion = load("ue_motion_evidence_pipeline")


class MotionEvidencePipelineTests(unittest.TestCase):
    def make_inputs(self, root: Path):
        video = root / "capture.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "color=c=black:s=64x64:r=30:d=0.1",
                "-an",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-y",
                str(video),
            ],
            check=True,
        )
        raw = video.read_bytes()
        video_manifest = {
            "schema_version": 1,
            "captured_at": "2026-07-29T09:10:00+09:00",
            "capture_method": "screen_recording_readonly",
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "expected_fps": 30,
            "observations": [
                {"frame": 0, "caption": "이동 루프"},
                {"frame": 1, "caption": "시각적 덜컥"},
                {"frame": 2, "caption": "이동 루프 복귀"},
            ],
        }
        log = root / "SB2.log"
        log.write_text(
            "\n".join(
                [
                    'LogBlueprintUserMessages: [ANIM_REC] "f"=1000,"sms"=1,"clip"=Jog_F,"trd"=90',
                    'LogBlueprintUserMessages: [ANIM_REC] "f"=1002,"sms"=1,"clip"=Jog_L,"trd"=90',
                    'LogBlueprintUserMessages: [ANIM_REC] "f"=1004,"sms"=1,"clip"=Jog_F,"trd"=90',
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        assets = {
            "schema_version": 1,
            "captured_at": "2026-07-29T09:11:00+09:00",
            "capture_method": "ue_readonly_dump",
            "project_revision": "p4-readonly-changelist-1234",
            "chooser_rows": [{"asset": "/Game/PC01/GroundMoving", "row": "LockOn-Left"}],
            "pose_search_databases": [{"asset": "/Game/PC01/PSD_GroundMoving", "continuing_pose_cost_bias": -0.01}],
            "animation_blueprint": {"asset": "/Game/PC01/PC_01_ABP", "compile_status": "read-only-observed"},
        }
        request = {
            "schema_version": 1,
            "hypothesis": {"id": "H1", "statement": "1프레임 이웃 클립 선택이 덜컥 원인이다."},
            "counterarguments": ["영상 덜컥이 카메라 움직임일 수 있다.", "로그 clip 필드가 최종 포즈를 뜻하지 않을 수 있다."],
            "historical_notes": [{"claim": "과거에도 경계각에서 1프레임 플리커가 있었다.", "source_ref": "historical-note-2026-06-15"}],
            "missing_candidates": ["포스트 프로세스 애니메이션 블루프린트", "루트 모션 보정"],
            "single_variable_check": {"variable": "ContinuingPoseCostBias", "baseline": -0.01, "candidate": -0.1},
            "anchors": [
                {"video_frame": 0, "anim_frame": 1000},
                {"video_frame": 2, "anim_frame": 1004},
            ],
        }
        return video, video_manifest, log, assets, request

    def test_real_30fps_video_and_two_anchors_align_visual_frames_to_anim_rec(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            video, video_manifest, log, assets, request = self.make_inputs(root)
            result = motion.build_review_bundle(video, video_manifest, log, assets, request)
            self.assertEqual(result["status"], "PASS_ALIGNMENT")
            self.assertEqual(result["verdict"], "HOLD_HERMES_REVIEW")
            self.assertEqual(result["aligned"][1]["anim_frame"], 1002)
            self.assertEqual(result["aligned"][1]["fields"]["clip"], "Jog_L")
            self.assertLessEqual(abs(result["probe"]["fps"] - 30.0), 0.001)
            report = result["report"]
            for heading in ["## 반박", "## 메모리 충돌", "## 빠진 후보", "## 단일변수 체크", "## 종합 판정"]:
                self.assertIn(heading, report)
            self.assertIn("CURRENT_MEASUREMENT", report)
            self.assertIn("HISTORICAL_NOTE", report)

    def test_missing_second_anchor_holds_instead_of_guessing_timeline(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            video, video_manifest, log, assets, request = self.make_inputs(root)
            changed = copy.deepcopy(request)
            changed["anchors"] = changed["anchors"][:1]
            with self.assertRaisesRegex(motion.MotionEvidenceError, "two synchronization anchors"):
                motion.build_review_bundle(video, video_manifest, log, assets, changed)

    def test_more_than_three_counterarguments_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            video, video_manifest, log, assets, request = self.make_inputs(root)
            changed = copy.deepcopy(request)
            changed["counterarguments"] = ["a", "b", "c", "d"]
            with self.assertRaisesRegex(motion.MotionEvidenceError, "at most 3"):
                motion.build_review_bundle(video, video_manifest, log, assets, changed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
