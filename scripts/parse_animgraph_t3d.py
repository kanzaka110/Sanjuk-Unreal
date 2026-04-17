"""Parse T3D export of PC_01_ABP AnimGraph and reconstruct the pose chain.

Usage:
    python scripts/parse_animgraph_t3d.py
    (reads scripts/_animgraph_t3d.txt)
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

T3D = Path(__file__).parent / "_animgraph_t3d.txt"

CATEGORY: tuple[tuple[str, str], ...] = (
    ("Output",          "AnimGraphNode_Root"),
    ("Inertialization", "Inertialization"),
    ("DeadBlending",    "DeadBlending"),
    ("MakeAdditive",    "MakeDynamicAdditive"),
    ("ApplyAdditive",   "ApplyMeshSpaceAdditive"),
    ("ApplyAdd(local)", "ApplyAdditive"),
    ("LinkedLayer",     "LinkedAnimLayer"),
    ("LinkedGraph",     "LinkedAnimGraph"),
    ("BlendStack",      "BlendStack"),
    ("PoseHistory",     "PoseSearchHistoryCollector"),
    ("StateMachine",    "StateMachine"),
    ("OffsetRoot",      "OffsetRootBone"),
    ("Slot",            "AnimGraphNode_Slot"),
    ("LayeredBlend",    "LayeredBoneBlend"),
    ("CachedSave",      "SaveCachedPose"),
    ("CachedUse",       "UseCachedPose"),
    ("TwoWayBlend",     "TwoWayBlend"),
    ("BlendSpace",      "BlendSpacePlayer"),
)


def cat_of(cls: str) -> str:
    for label, token in CATEGORY:
        if token.lower() in cls.lower():
            return label
    return "?"


@dataclass
class Node:
    name: str
    cls: str
    x: int = 0
    y: int = 0
    # pin_name -> list of (target_node_name, target_pin_id)
    links: dict[str, list[tuple[str, str]]] = field(default_factory=dict)
    pin_directions: dict[str, str] = field(default_factory=dict)

    @property
    def cat(self) -> str:
        return cat_of(self.cls)


def parse(path: Path) -> dict[str, Node]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.split("\n")

    nodes: dict[str, Node] = {}
    current: Node | None = None
    depth = 0

    begin_re = re.compile(
        r"^Begin Object Class=/Script/\S+\.(\S+?) Name=\"([^\"]+)\""
    )
    pos_x_re = re.compile(r"^\s*NodePosX=(-?\d+)")
    pos_y_re = re.compile(r"^\s*NodePosY=(-?\d+)")
    pin_re = re.compile(r"^\s*CustomProperties Pin \((.*)\)\s*$")

    for ln in lines:
        stripped = ln.strip()
        if stripped.startswith("Begin Object"):
            if depth == 0 and "Class=" in stripped:
                m = begin_re.match(stripped)
                if m:
                    cls, name = m.group(1), m.group(2)
                    if cls.startswith(("AnimGraphNode_",
                                       "SBAnimGraphNode_")):
                        current = Node(name=name, cls=cls)
                        nodes[name] = current
            depth += 1
            continue
        if stripped == "End Object":
            depth -= 1
            if depth <= 0:
                depth = 0
                current = None
            continue
        if current is None:
            continue

        mx = pos_x_re.match(ln)
        if mx:
            current.x = int(mx.group(1))
            continue
        my = pos_y_re.match(ln)
        if my:
            current.y = int(my.group(1))
            continue

        mp = pin_re.match(ln)
        if not mp:
            continue
        body = mp.group(1)

        pin_name_m = re.search(r'PinName="([^"]+)"', body)
        if not pin_name_m:
            continue
        pin_name = pin_name_m.group(1)

        dir_m = re.search(r'Direction="([^"]+)"', body)
        if dir_m:
            current.pin_directions[pin_name] = dir_m.group(1)

        linked_m = re.search(r"LinkedTo=\(([^)]*)\)", body)
        if not linked_m:
            continue
        linked_body = linked_m.group(1).strip()
        if not linked_body:
            continue

        targets: list[tuple[str, str]] = []
        for piece in linked_body.split(","):
            piece = piece.strip()
            if not piece:
                continue
            parts = piece.split()
            if len(parts) >= 2:
                targets.append((parts[0], parts[1]))
        if targets:
            current.links[pin_name] = targets

    return nodes


def render_chain(nodes: dict[str, Node]) -> None:
    root = next((n for n in nodes.values()
                 if n.cls == "AnimGraphNode_Root"), None)
    if not root:
        print("No root")
        return

    print("=" * 92)
    print("전체 노드 (X 내림차순 = 오른쪽=Output 쪽)")
    print("=" * 92)
    print(f"{'X':>6} {'Y':>6}  {'cat':<15} {'class':<42} name")
    print("-" * 92)
    for n in sorted(nodes.values(),
                    key=lambda n: (-n.x, n.y)):
        print(f"{n.x:>6} {n.y:>6}  {n.cat:<15} {n.cls:<42} {n.name}")

    print("\n" + "=" * 92)
    print("역방향 체인 (Output → 업스트림)")
    print("=" * 92)

    visited: set[str] = set()
    queue: list[tuple[Node, int, str]] = [(root, 0, "Result")]
    while queue:
        node, depth, via = queue.pop(0)
        if node.name in visited:
            continue
        visited.add(node.name)
        indent = "  " * depth
        mark = "★" if node.cat in ("Inertialization", "DeadBlending") else "·"
        print(f"{indent}{mark} [{node.cat:15s}] {node.cls}  "
              f"(x={node.x}) <via {via}>")
        for pin, targets in node.links.items():
            d = node.pin_directions.get(pin, "EGPD_Input")
            if d == "EGPD_Output":
                continue
            for tname, _ in targets:
                t = nodes.get(tname)
                if t:
                    queue.append((t, depth + 1, pin))

    print("\n" + "=" * 92)
    print("Inertialization / DeadBlending 위치 분석")
    print("=" * 92)

    for target_cls in ("AnimGraphNode_Inertialization",
                       "AnimGraphNode_DeadBlending"):
        node = next((n for n in nodes.values() if n.cls == target_cls), None)
        if not node:
            print(f"\n  [{target_cls}] 없음")
            continue
        print(f"\n  [{node.cls}]  x={node.x}  y={node.y}  name={node.name}")

        src = []
        for pin, targets in node.links.items():
            d = node.pin_directions.get(pin, "EGPD_Input")
            if d != "EGPD_Output":
                for tn, _ in targets:
                    t = nodes.get(tn)
                    if t:
                        src.append((pin, t))
        print("    업스트림(Source):")
        for pin, t in src:
            print(f"      ← [{t.cat:15s}] {t.cls}  (x={t.x})  via '{pin}'")

        downs: list[tuple[str, Node]] = []
        for other in nodes.values():
            for pin, targets in other.links.items():
                for tn, _ in targets:
                    if tn == node.name:
                        downs.append((pin, other))
        print("    다운스트림(Consumer):")
        for pin, o in downs:
            print(f"      → [{o.cat:15s}] {o.cls}  (x={o.x})  via '{pin}'")


def main() -> None:
    if not T3D.exists():
        print(f"T3D not found: {T3D}")
        return
    nodes = parse(T3D)
    print(f"parsed {len(nodes)} AnimGraph nodes\n")
    render_chain(nodes)


if __name__ == "__main__":
    main()
