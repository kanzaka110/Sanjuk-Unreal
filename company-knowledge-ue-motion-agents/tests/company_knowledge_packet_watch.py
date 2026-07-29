#!/usr/bin/env python3
"""Silent no-LLM receiver for validated company knowledge packets."""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from company_knowledge_packet import (
    DEFAULT_RAW_ROOT,
    DEFAULT_STORE_ROOT,
    InvalidPacket,
    PacketConflict,
    PacketStore,
    import_from_raw_cache,
)
from company_knowledge_case_stager import StagingError, stage_group

DEFAULT_STAGING_ROOT = Path(
    "/root/.hermes/second-brain/Projects/Hermes/Company-Knowledge-Staging"
)


def run_once(
    raw_root: Path | str = DEFAULT_RAW_ROOT,
    store_root: Path | str = DEFAULT_STORE_ROOT,
    staging_root: Path | str = DEFAULT_STAGING_ROOT,
) -> str:
    store_path = Path(store_root)
    result = import_from_raw_cache(Path(raw_root), PacketStore(store_path))
    staged_new = 0
    staged_groups = 0
    for group_dir in sorted(store_path.iterdir(), key=lambda item: item.name):
        if not group_dir.is_dir() or group_dir.is_symlink():
            continue
        staged = stage_group(group_dir, staging_root)
        staged_groups += 1
        if staged["result"] == "new":
            staged_new += 1
    if result["new"] == 0 and staged_new == 0:
        return ""
    return (
        "PASS Company Knowledge Packet 수신 "
        f"new={result['new']} groups={result['groups']} packet_files={result['packet_files']} "
        f"staged_new={staged_new} staged_groups={staged_groups} promotion=HOLD_HUMAN_REVIEW"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--store", type=Path, default=DEFAULT_STORE_ROOT)
    parser.add_argument("--staging-root", type=Path, default=DEFAULT_STAGING_ROOT)
    args = parser.parse_args()
    try:
        message = run_once(args.raw_root, args.store, args.staging_root)
        if message:
            print(message)
        return 0
    except (InvalidPacket, PacketConflict, StagingError, OSError, UnicodeError) as exc:
        fingerprint = hashlib.sha256(str(exc).encode("utf-8")).hexdigest()[:12]
        print(f"HOLD Company Knowledge Packet: {type(exc).__name__} ({fingerprint})")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
