"""PC_01_ABP AnimGraph에서 Inertialization / DeadBlending의 위치를
좌표 + 주변 노드로 추정.

Run inside Unreal Editor:
    exec(open("C:/Dev/Sanjuk-Unreal/scripts/locate_inertialization.py").read())
"""
from __future__ import annotations

import unreal

ABP_PATH: str = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"

CATEGORY_HINTS: tuple[tuple[str, str], ...] = (
    ("Output",          "AnimGraphNode_Root"),
    ("Inertialization", "Inertialization"),
    ("DeadBlending",    "DeadBlending"),
    ("MakeAdditive",    "MakeDynamicAdditive"),
    ("ApplyAdditive",   "ApplyAdditive"),
    ("LinkedLayer",     "LinkedAnimLayer"),
    ("LinkedGraph",     "LinkedAnimGraph"),
    ("BlendStack",      "BlendStack"),
    ("MotionMatch",     "MotionMatching"),
    ("PoseSearch",      "PoseSearch"),
    ("ChooserPlayer",   "ChooserPlayer"),
    ("StateMachine",    "StateMachine"),
    ("IK_FootPlace",    "FootPlacement"),
    ("IK_Rig",          "IKRig"),
    ("IK_ControlRig",   "ControlRig"),
    ("OffsetRoot",      "OffsetRootBone"),
    ("Slot",            "Slot"),
    ("LayeredBlend",    "LayeredBoneBlend"),
    ("CachedPose",      "CachedPose"),
    ("Blend",           "Blend"),
)

POS_PROPS: tuple[str, ...] = (
    "node_pos_x", "node_pos_y",
    "NodePosX", "NodePosY",
)


def categorize(cls_name: str) -> str:
    for label, token in CATEGORY_HINTS:
        if token.lower() in cls_name.lower():
            return label
    return "?"


def try_props(obj, candidates: tuple[str, ...]) -> int | None:
    for p in candidates:
        try:
            v = obj.get_editor_property(p)
            if v is not None:
                return int(v)
        except Exception:
            continue
    return None


def get_pos(node) -> tuple[int | None, int | None]:
    x = try_props(node, ("node_pos_x", "NodePosX"))
    y = try_props(node, ("node_pos_y", "NodePosY"))
    return (x, y)


def get_comment(node) -> str:
    for p in ("node_comment", "NodeComment"):
        try:
            v = node.get_editor_property(p)
            if v:
                return str(v)
        except Exception:
            continue
    return ""


def main() -> None:
    abp = unreal.load_asset(ABP_PATH)
    if not abp:
        print("[ERROR] load fail")
        return

    graphs = list(abp.get_animation_graphs())
    main_g = next((g for g in graphs if g.get_name() == "AnimGraph"), None)
    if not main_g:
        print("AnimGraph 없음")
        return

    nodes = list(main_g.get_graph_nodes_of_class(unreal.AnimGraphNode_Base))
    print(f"[AnimGraph] nodes={len(nodes)}\n")

    items: list[dict] = []
    for n in nodes:
        try:
            cls = n.get_class().get_name()
            nid = n.get_name()
            x, y = get_pos(n)
            items.append({
                "cat": categorize(cls),
                "cls": cls,
                "nid": nid,
                "x": x,
                "y": y,
                "cmt": get_comment(n),
            })
        except Exception:
            pass

    # X 내림차순 (오른쪽 = 다운스트림 = Output 쪽)
    items.sort(
        key=lambda r: (r["x"] is None, -(r["x"] or 0), r["y"] or 0)
    )

    print("=" * 92)
    print(f"{'X':>7} {'Y':>7}  {'카테고리':<16} {'클래스':<38} {'주석'}")
    print("=" * 92)
    for r in items:
        xs = f"{r['x']:>7}" if r["x"] is not None else "      ?"
        ys = f"{r['y']:>7}" if r["y"] is not None else "      ?"
        cls = r["cls"][:38]
        cmt = r["cmt"][:30]
        mark = "★" if r["cat"] in ("Inertialization", "DeadBlending") else " "
        print(f"{xs} {ys}  {r['cat']:<16}{mark} {cls:<38} {cmt}")

    # 관심 노드 요약
    print("\n" + "=" * 92)
    print("Inertialization / DeadBlending 주변 분석")
    print("=" * 92)
    root = next((r for r in items if r["cat"] == "Output"), None)
    if root:
        print(f"  Root(Output) 좌표: ({root['x']}, {root['y']})")

    for key in ("Inertialization", "DeadBlending"):
        tgt = next((r for r in items if r["cat"] == key), None)
        if not tgt:
            continue
        print(f"\n  [{key}] {tgt['cls']}  @({tgt['x']}, {tgt['y']})")
        if tgt["cmt"]:
            print(f"    주석: {tgt['cmt']}")
        if tgt["x"] is None:
            continue
        # X 좌표 ±200 근방 노드
        nearby_x = [
            r for r in items
            if r["x"] is not None
            and r is not tgt
            and abs(r["x"] - tgt["x"]) <= 300
        ]
        nearby_x.sort(key=lambda r: r["x"])
        print(f"    X±300 근방 노드 (왼쪽→오른쪽):")
        for r in nearby_x:
            print(f"      x={r['x']:>6} y={r['y']:>6}  "
                  f"{r['cat']:<15} {r['cls']}")
        if root:
            direct_distance_x = tgt["x"] - root["x"]
            print(f"    Root과의 X 거리: {direct_distance_x} "
                  f"({'Root 앞(업스트림)' if direct_distance_x < 0 else 'Root 뒤?'})")


main()
