#!/usr/bin/env python3
"""ABP 백업/롤백 CLI — Tuner 직전 자동 호출 + 사용자 수동 호출 둘 다 지원.

서브명령:
  backup  <asset> [label]        — 새 백업 (5종 dump 묶음)
  list    <asset>                — 백업 목록 (timestamp 역순)
  diff    <asset> <ts>           — 현재 vs 백업 비교 (변수/SM/그래프 메타)
  restore <asset> <ts> [--apply] — 변수 default 복원 (dry-run 기본, --apply 로 실제)
  prune   <asset> [--days 7]     — N일 이상된 백업 삭제

백업 위치: .claude/state/backups/<ASSET_NAME>/<TIMESTAMP[_label]>/

핵심 한계:
  - 변수 default 복원만 안전. 노드 추가/삭제, transition rule chain 변경은
    Monolith 한계로 자동 복원 불가 (사용자 에디터 수동).
  - SM transition topology, Chooser ResultsStructs, set_pin_default 등은 plan 만 출력.

사용 예:
    py scripts/abp_backup.py backup /Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP istransition-test
    py scripts/abp_backup.py list   /Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP
    py scripts/abp_backup.py diff   /Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP 20260518_120000
    py scripts/abp_backup.py restore /Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP istransition-test --apply
    py scripts/abp_backup.py prune  /Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP --days 14
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from monolith_helpers import MonolithClient, MonolithError  # type: ignore


def fix_msys_asset_path(asset: str) -> str:
    """Git Bash MSYS path 변환 복구.

    Git Bash 가 `/Game/...` 인자를 `C:/Program Files/Git/Game/...` 등으로 변환.
    UE asset path 가 망가지면 `/Game/...` 로 복구.
    """
    for prefix in ("C:/Program Files/Git/Game/", "C:\\Program Files\\Git\\Game\\"):
        if asset.startswith(prefix):
            tail = asset[len(prefix):].replace("\\", "/")
            return "/Game/" + tail
    return asset


def cmd_backup(args: argparse.Namespace) -> int:
    cli = MonolithClient(fix_msys_asset_path(args.asset))
    result = cli.backup(label=args.label or "")
    print(f"✓ backup: {result['path']}")
    print(f"  timestamp: {result['timestamp']}")
    if result.get("label"):
        print(f"  label    : {result['label']}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    cli = MonolithClient(fix_msys_asset_path(args.asset))
    backups = cli.list_backups()
    if not backups:
        print("(no backups)")
        return 0
    print(f"{'timestamp':<20} {'label':<24} dir")
    print("-" * 80)
    for b in backups:
        ts = b.get("timestamp", "?")
        lb = b.get("label") or ""
        print(f"{ts:<20} {lb:<24} {b['dir']}")
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    cli = MonolithClient(fix_msys_asset_path(args.asset))
    try:
        diff = cli.diff_against_backup(args.timestamp)
    except MonolithError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 2
    print(f"backup dir       : {diff['backup_dir']}")
    print(f"abp meta changed : {diff['abp_meta_changed']}")
    print(f"vars added       : {diff['variables_added']}")
    print(f"vars removed     : {diff['variables_removed']}")
    print(f"vars def changed : {diff['variables_changed_default']}")
    print(
        f"sm transitions   : {diff['sm_transition_count_old']} → "
        f"{diff['sm_transition_count_new']}"
    )
    return 0


def cmd_restore(args: argparse.Namespace) -> int:
    cli = MonolithClient(fix_msys_asset_path(args.asset))
    try:
        plan = cli.rollback(args.timestamp, dry_run=not args.apply)
    except MonolithError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 2
    print(f"backup dir : {plan['backup_dir']}")
    print(f"dry_run    : {plan['dry_run']}")
    print(f"operations ({len(plan['operations'])}):")
    for op in plan["operations"]:
        print(f"  - {op['type']}  {op.get('variable','-')} → {op.get('to','-')}")
    if plan["unsupported"]:
        print(f"unsupported ({len(plan['unsupported'])}):")
        for u in plan["unsupported"]:
            print(f"  - {u['type']}  ({u.get('reason')})")
    if not args.apply:
        print("\n[dry-run] 적용하려면 --apply 추가")
    else:
        print(f"\n[applied] commit: {plan.get('commit', {}).get('compile')}")
        for a in plan.get("applied", []):
            if "error" in a:
                print(f"  ✗ {a['op']['variable']}: {a['error']}")
            else:
                print(f"  ✓ {a['op']['variable']}")
    return 0


def cmd_prune(args: argparse.Namespace) -> int:
    cli = MonolithClient(fix_msys_asset_path(args.asset))
    backups = cli.list_backups()
    cutoff = datetime.now() - timedelta(days=args.days)
    removed = 0
    for b in backups:
        created = b.get("created_at", "")
        try:
            ts = datetime.fromisoformat(created)
        except ValueError:
            continue
        if ts < cutoff:
            shutil.rmtree(b["dir"], ignore_errors=True)
            print(f"✗ removed (>{args.days}d): {b['dir']}")
            removed += 1
    print(f"\npruned {removed}/{len(backups)} backups")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_backup = sub.add_parser("backup", help="새 백업")
    p_backup.add_argument("asset")
    p_backup.add_argument("label", nargs="?", default="")

    p_list = sub.add_parser("list", help="백업 목록")
    p_list.add_argument("asset")

    p_diff = sub.add_parser("diff", help="현재 vs 백업")
    p_diff.add_argument("asset")
    p_diff.add_argument("timestamp", help="timestamp 또는 label 부분 일치")

    p_restore = sub.add_parser("restore", help="변수 default 복원")
    p_restore.add_argument("asset")
    p_restore.add_argument("timestamp")
    p_restore.add_argument("--apply", action="store_true", help="실제 적용 (없으면 dry-run)")

    p_prune = sub.add_parser("prune", help="오래된 백업 삭제")
    p_prune.add_argument("asset")
    p_prune.add_argument("--days", type=int, default=7)

    args = ap.parse_args()
    return {
        "backup":  cmd_backup,
        "list":    cmd_list,
        "diff":    cmd_diff,
        "restore": cmd_restore,
        "prune":   cmd_prune,
    }[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
