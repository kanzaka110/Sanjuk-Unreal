"""AnimGraph의 22개 노드 전체를 분류해서 나열 + pin API probe.

Run inside Unreal Editor:
    exec(open("C:/Dev/Sanjuk-Unreal/scripts/dump_animgraph_nodes.py").read())
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
    ("IK_TwoBone",      "TwoBoneIK"),
    ("IK_FABRIK",       "Fabrik"),
    ("IK_LegIK",        "LegIK"),
    ("IK_Rig",          "IKRig"),
    ("IK_ControlRig",   "ControlRig"),
    ("IK_ModifyBone",   "ModifyBone"),
    ("SlopeWarp",       "SlopeWarping"),
    ("StrideWarp",      "StrideWarping"),
    ("OrientWarp",      "OrientationWarping"),
    ("OffsetRoot",      "OffsetRootBone"),
    ("Slot",            "Slot"),
    ("LayeredBlend",    "LayeredBoneBlend"),
    ("CachedPose",      "CachedPose"),
    ("SB_BoneScale",    "SBAnimGraphNode_BoneScale"),
    ("SB_HitBones",     "SBAnimGraphNode_HitBones"),
    ("SB_SlopeWarp",    "SBAnimGraphNode_SlopeWarping"),
    ("Blend",           "Blend"),
)


def categorize(cls_name: str) -> str:
    for label, token in CATEGORY_HINTS:
        if token.lower() in cls_name.lower():
            return label
    return "?"


def probe_pin_api(node) -> None:
    print("\n" + "-" * 70)
    print(f"[pin probe] node={node.get_name()}  class={node.get_class().get_name()}")
    print("-" * 70)

    print("• dir(node) 중 'pin' 포함:")
    for n in dir(node):
        if "pin" in n.lower():
            print("    " + n)

    for meth in ("get_all_pins", "pins"):
        try:
            fn = getattr(node, meth, None)
            if fn is None:
                print(f"  {meth}: not found")
                continue
            if callable(fn):
                val = fn()
            else:
                val = fn
            n = len(val) if hasattr(val, "__len__") else "(?)"
            print(f"  {meth} -> {n}   type={type(val).__name__}")
            if val:
                first = val[0]
                print(f"  first pin type={type(first).__name__}")
                print("  dir(pin) 중 link/connect/direction:")
                for nm in dir(first):
                    low = nm.lower()
                    if ("link" in low or "connect" in low
                            or "direction" in low or "name" in low
                            or "type" in low):
                        if not nm.startswith("_"):
                            print("    " + nm)
        except Exception as e:
            print(f"  {meth} err: {type(e).__name__}: {str(e)[:80]}")


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
    print(f"[AnimGraph] nodes={len(nodes)}")
    print()

    rows: list[tuple[str, str, str]] = []
    for n in nodes:
        try:
            cls = n.get_class().get_name()
            nid = n.get_name()
            cat = categorize(cls)
            rows.append((cat, cls, nid))
        except Exception:
            pass

    rows.sort(key=lambda r: (r[0] == "?", r[0]))
    print("=" * 70)
    print("카테고리  | 클래스                         | 인스턴스")
    print("=" * 70)
    for cat, cls, nid in rows:
        print(f"  {cat:14s} | {cls:32s} | {nid}")

    print("\n카테고리 집계:")
    from collections import Counter
    counts = Counter(r[0] for r in rows)
    for cat, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {cat:14s} x {n}")

    probe_pin_api(nodes[0])


main()
