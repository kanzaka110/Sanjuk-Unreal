"""Walk PC_01_ABP AnimGraph from Output Pose backwards to identify
the optimal Inertialization insertion point.

Run inside Unreal Editor:
    exec(open("C:/Dev/Sanjuk-Unreal/scripts/find_inertialization_spot.py").read())
"""
from __future__ import annotations

import unreal

ABP_PATH: str = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
MAX_DEPTH: int = 120

CATEGORY_HINTS: tuple[tuple[str, str], ...] = (
    ("Output",          "AnimGraphNode_Root"),
    ("StateResult",     "AnimGraphNode_StateResult"),
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
    ("IK_CCDIK",        "CCDIK"),
    ("IK_Rig",          "IKRig"),
    ("IK_ControlRig",   "ControlRig"),
    ("IK_ModifyBone",   "ModifyBone"),
    ("SlopeWarp",       "SlopeWarping"),
    ("StrideWarp",      "StrideWarping"),
    ("OrientWarp",      "OrientationWarping"),
    ("OffsetRoot",      "OffsetRootBone"),
    ("Slot",            "Slot"),
    ("LayeredBlend",    "LayeredBoneBlend"),
    ("BlendProfile",    "BlendProfileLayeredBlend"),
    ("SubInst",         "SubInstance"),
    ("CachedPose",      "CachedPose"),
    ("RigidBody",       "RigidBody"),
    ("KawaiiPhys",      "KawaiiPhysics"),
    ("Sync",            "Sync"),
    ("SB_BoneScale",    "SBAnimGraphNode_BoneScale"),
    ("SB_HitBones",     "SBAnimGraphNode_HitBones"),
    ("SB_SlopeWarp",    "SBAnimGraphNode_SlopeWarping"),
    ("Mirror",          "Mirror"),
    ("Blend",           "Blend"),
    ("SequencePlayer",  "SequencePlayer"),
    ("SequenceEvaluator", "SequenceEvaluator"),
    ("Transition",      "TransitionResult"),
)


def categorize(cls_name: str) -> str:
    for label, token in CATEGORY_HINTS:
        if token.lower() in cls_name.lower():
            return label
    return "?"


def graph_nodes(graph) -> list:
    try:
        return list(graph.get_graph_nodes_of_class(unreal.AnimGraphNode_Base))
    except Exception:
        pass
    all_nodes: list = []
    for cname in dir(unreal):
        if not (cname.startswith("AnimGraphNode_")
                or cname.startswith("SBAnimGraphNode_")):
            continue
        try:
            cls = getattr(unreal, cname)
            found = graph.get_graph_nodes_of_class(cls)
            for n in found:
                if n not in all_nodes:
                    all_nodes.append(n)
        except Exception:
            continue
    return all_nodes


def input_driver_nodes(node) -> list:
    out: list = []
    try:
        pins = node.get_all_pins()
    except Exception:
        return out
    for pin in pins:
        try:
            if pin.get_pin_direction() != unreal.EdGraphPinDirection.INPUT:
                continue
            for linked in (pin.get_linked_pins() or []):
                owner = linked.get_owning_node()
                if owner and owner not in out:
                    out.append(owner)
        except Exception:
            continue
    return out


def find_root(nodes: list):
    for n in nodes:
        try:
            cls = n.get_class().get_name()
            if cls in ("AnimGraphNode_Root", "AnimGraphNode_StateResult"):
                return n
        except Exception:
            pass
    return None


def dump_graph_chain(graph) -> bool:
    nodes = graph_nodes(graph)
    gname = graph.get_name()
    if not nodes:
        return False

    root = find_root(nodes)
    if not root:
        return False

    print("\n" + "=" * 70)
    print(f"[graph] {gname}   nodes={len(nodes)}")
    print("=" * 70)

    visited: set[str] = set()
    queue: list[tuple[object, int]] = [(root, 0)]
    chain: list[tuple[int, str, str, str]] = []

    while queue:
        node, depth = queue.pop(0)
        if depth > MAX_DEPTH:
            continue
        try:
            nid = node.get_name()
        except Exception:
            continue
        if nid in visited:
            continue
        visited.add(nid)
        try:
            cls = node.get_class().get_name()
        except Exception:
            cls = "Unknown"
        chain.append((depth, categorize(cls), cls, nid))
        for up in input_driver_nodes(node):
            queue.append((up, depth + 1))

    for depth, cat, cls, nid in chain:
        indent = "  " * depth
        mark = "*" if cat != "?" else "."
        short_nid = nid[:40]
        print(f"{indent}{mark} [{cat:14s}] {cls}  #{short_nid}")

    seen: list[str] = []
    for _, cat, _, _ in chain:
        if cat != "?" and cat not in seen:
            seen.append(cat)
    print("\n카테고리 순서:", " -> ".join(seen))

    has_inert = any(c in ("Inertialization", "DeadBlending")
                    for _, c, _, _ in chain)
    print("Inertialization/DeadBlending:", "있음 ✓" if has_inert else "없음 ✗")
    return True


def main() -> None:
    abp = unreal.load_asset(ABP_PATH)
    if not abp:
        print("[ERROR] load fail")
        return

    graphs = list(abp.get_animation_graphs())
    print(f"[asset] {abp.get_name()}  anim_graphs={len(graphs)}")

    shown = 0
    skipped: list[str] = []
    for g in graphs:
        ok = dump_graph_chain(g)
        if ok:
            shown += 1
        else:
            try:
                skipped.append(g.get_name())
            except Exception:
                pass

    print("\n" + "=" * 70)
    print(f"표시된 그래프: {shown} / 전체 {len(graphs)}")
    if skipped:
        print("생략된 그래프 (노드 없음 or Root 없음):")
        for s in skipped[:20]:
            print("  ·", s)
        if len(skipped) > 20:
            print(f"  ... (+{len(skipped)-20} more)")


main()
