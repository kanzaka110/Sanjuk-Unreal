#!/usr/bin/env python3
"""Rebuild backup_old_id -> current_new_id mapping from positions + class.

After Phase 2 + 2b, the graph holds the right node count but our cached map
might be stale. This script reads the live graph and the backup, matches by
(class, x, y) tuples, and writes a fresh ABRR_id_map.json.

K2Node_GetEnumeratorNameAsString in backup is matched to K2Node_CallFunction
in live graph (because we replaced enum-name nodes with GetEnumeratorName fn).
"""
from __future__ import annotations

import json
from pathlib import Path

BACKUP = Path(r"C:\Dev\Sanjuk-Unreal\Saved\PROBE_AnimRewindRecorderEmit_consolidated_20260514.json")
LIVE = Path(r"C:\Dev\Sanjuk-Unreal\Saved\ABRR_now_text.json")
MAP_OUT = Path(r"C:\Dev\Sanjuk-Unreal\Saved\ABRR_id_map.json")


def main() -> None:
    bk = json.loads(BACKUP.read_text(encoding="utf-8-sig"))
    lv = json.loads(LIVE.read_text(encoding="utf-8-sig"))

    bk_nodes = bk["nodes"]
    lv_nodes = lv["nodes"]
    print(f"Backup: {len(bk_nodes)}, Live: {len(lv_nodes)}")

    # Build live index by (class, x, y)
    lv_index: dict[tuple[str, int, int], list[str]] = {}
    for n in lv_nodes:
        key = (n["class"], int(n["pos"][0]), int(n["pos"][1]))
        lv_index.setdefault(key, []).append(n["id"])

    # Substitution: backup class K2Node_GetEnumeratorNameAsString -> live class K2Node_CallFunction
    def candidate_keys(bk_node: dict) -> list[tuple[str, int, int]]:
        cls = bk_node["class"]
        pos = (int(bk_node["pos"][0]), int(bk_node["pos"][1]))
        keys = [(cls, *pos)]
        if cls == "K2Node_GetEnumeratorNameAsString":
            keys.append(("K2Node_CallFunction", *pos))
        return keys

    id_map: dict[str, str] = {}
    misses: list[str] = []

    # Pass 1: exact match per (class, pos)
    for n in bk_nodes:
        for key in candidate_keys(n):
            if key in lv_index and lv_index[key]:
                id_map[n["id"]] = lv_index[key].pop(0)
                break
        else:
            misses.append(n["id"])

    # Pass 2: match unique-class singletons regardless of position
    for missed_id in list(misses):
        bk_node = next(n for n in bk_nodes if n["id"] == missed_id)
        cls = bk_node["class"]
        candidates = [(k, ids) for k, ids in lv_index.items() if k[0] == cls and ids]
        if len(candidates) == 1 and len(candidates[0][1]) == 1:
            key, ids = candidates[0]
            id_map[missed_id] = ids[0]
            ids.clear()
            misses.remove(missed_id)
            print(f"Pass2 matched {missed_id} -> {key} (single)")

    print(f"\nMatched: {len(id_map)}")
    print(f"Misses:  {len(misses)} -> {misses[:6]}")
    print(f"Unmatched live nodes:")
    leftover = sum(len(v) for v in lv_index.values())
    print(f"  count={leftover}")
    for k, ids in lv_index.items():
        if ids:
            print(f"  {k} -> {ids}")

    MAP_OUT.write_text(json.dumps(id_map, indent=2, ensure_ascii=False), encoding="utf-8-sig")
    print(f"\nWritten: {MAP_OUT} ({len(id_map)} entries)")


if __name__ == "__main__":
    main()
