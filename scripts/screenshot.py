#!/usr/bin/env python3
"""에디터/PIE viewport 스크린샷 — Tuner 변경 후 시각 검증용.

editor.run_console_command("HighResShot WxH") 로 캡처 → Saved/Screenshots/WindowsEditor/ 의
새 PNG 자동 감지 + (옵션) 라벨/타임스탬프로 별도 디렉토리 복사.

사용:
    py scripts/screenshot.py                                   # 1920x1080 기본
    py scripts/screenshot.py --resolution 2560x1440
    py scripts/screenshot.py --label istransition-before --copy dumps/screenshots
    py scripts/screenshot.py --before-after istransition       # before/after 2장 묶음
"""
from __future__ import annotations

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from monolith_helpers import MonolithClient  # type: ignore


def parse_resolution(s: str) -> tuple[int, int]:
    parts = s.lower().split("x")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError(f"resolution 형식 X: {s!r} (예: 1920x1080)")
    return int(parts[0]), int(parts[1])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument(
        "--asset",
        default="/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP",
        help="MonolithClient asset path (실제 캡처와 무관, 헬퍼 초기화용)",
    )
    ap.add_argument(
        "--resolution",
        type=parse_resolution,
        default=(1920, 1080),
        help="WxH 형식 (default 1920x1080)",
    )
    ap.add_argument("--label", default="", help="복사본 파일명 suffix")
    ap.add_argument("--copy", help="복사 대상 디렉토리 (없으면 원본 경로만 출력)")
    ap.add_argument(
        "--sb2-root",
        default=r"E:\Perforce\SB2\Workspace\Internal\SB2",
        help="SB2 프로젝트 루트 (Saved/Screenshots 탐색용)",
    )
    ap.add_argument(
        "--before-after",
        metavar="LABEL",
        help="before/after 2장 캡처. 사이에 사용자 변경 작업 대기 (Enter)",
    )
    args = ap.parse_args()

    cli = MonolithClient(args.asset)

    if args.before_after:
        base = args.before_after
        copy_dir = args.copy or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "dumps", "screenshots",
        )
        os.makedirs(copy_dir, exist_ok=True)

        print(f"[before] {base} 캡처...")
        before = cli.screenshot(
            args.resolution, label=f"{base}_before",
            sb2_project_root=args.sb2_root, copy_to=copy_dir,
        )
        print(f"  ✓ {before.get('copied_to') or before.get('captured_path')}")

        print(f"\n변경 작업 수행 후 [Enter] — Ctrl+C 로 중단")
        try:
            input()
        except KeyboardInterrupt:
            print("\n[중단]")
            return 1

        print(f"[after] {base} 캡처...")
        after = cli.screenshot(
            args.resolution, label=f"{base}_after",
            sb2_project_root=args.sb2_root, copy_to=copy_dir,
        )
        print(f"  ✓ {after.get('copied_to') or after.get('captured_path')}")

        # 카메라 변동 자동 비교
        if before.get("camera_meta_path") and after.get("camera_meta_path"):
            cmp_result = MonolithClient.compare_camera(
                before["camera_meta_path"], after["camera_meta_path"]
            )
            print(f"\n[camera drift]")
            print(f"  location : {cmp_result['drift_location_cm']} cm")
            print(f"  rotation : {cmp_result['drift_rotation_deg']} deg")
            print(f"  fov      : {cmp_result['drift_fov_deg']} deg")
            if cmp_result["warning"]:
                print(f"  {cmp_result['warning']}")
            else:
                print(f"  ✓ 카메라 동일 — mesh 차이가 진짜 변경")
        return 0

    result = cli.screenshot(
        args.resolution,
        label=args.label,
        sb2_project_root=args.sb2_root,
        copy_to=args.copy,
    )
    if not result.get("captured_path"):
        print(f"[FAIL] 캡처 PNG 못 찾음. 폴링 {result.get('elapsed_seconds')}s", file=sys.stderr)
        return 2
    print(f"✓ captured: {result['captured_path']}")
    if result.get("copied_to"):
        print(f"  copied  : {result['copied_to']}")
    print(f"  elapsed : {result['elapsed_seconds']}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
