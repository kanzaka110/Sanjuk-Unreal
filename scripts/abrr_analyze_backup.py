#!/usr/bin/env python3
"""Analyze backup JSON: count node classes, find unusual ones."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

BACKUP = Path(r"C:\Dev\Sanjuk-Unreal\Saved\PROBE_AnimRewindRecorderEmit_consolidated_20260514.json")


def main() -> None:
    data = json.loads(BACKUP.read_text(encoding="utf-8"))
    nodes = data["nodes"]
    print(f"Total nodes: {len(nodes)}")
    classes = Counter(n["class"] for n in nodes)
    for cls, n in sorted(classes.items(), key=lambda kv: -kv[1]):
        print(f"  {n:3d}  {cls}")

    print("\n--- Detailed per-class probes ---")
    for n in nodes:
        cls = n["class"]
        # Examples of each class
        if cls == "K2Node_VariableGet":
            # check primary output pin
            pin = n["pins"][0]
            split = ("_X" in pin["name"] or "_Y" in pin["name"] or "_Z" in pin["name"])
            if split:
                print(f"  SPLIT VarGet {n['id']}: pins={[p['name'] for p in n['pins']]}")

    print("\n--- All function_class references in CallFunction ---")
    fc_set = set()
    for n in nodes:
        if n["class"] == "K2Node_CallFunction":
            fn = n.get("function", "")
            fcl = n.get("function_class", "")
            fc_set.add((fcl, fn))
    for fcl, fn in sorted(fc_set):
        print(f"  {fcl or '(default)':<40} {fn}")


if __name__ == "__main__":
    main()
