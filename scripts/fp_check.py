"""FootPlacement 바인딩 진단 — get_animation_graphs 사용."""
import unreal

LAYER_PATH = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK"


def sep(title: str) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


asset = unreal.load_asset(LAYER_PATH)
if not asset:
    print(f"[ERR] load failed: {LAYER_PATH}")
    raise SystemExit

bel = unreal.BlueprintEditorLibrary

sep("에셋 기본")
print(f"  name = {asset.get_name()}")

# 1. 애니메이션 그래프 목록
sep("애니메이션 그래프 (get_animation_graphs)")
try:
    ag = list(asset.get_animation_graphs() or [])
    print(f"  count = {len(ag)}")
    for g in ag:
        try:
            nodes = list(g.get_editor_property("nodes") or [])
        except Exception:
            nodes = []
        print(f"    {g.get_name():40s} nodes={len(nodes)} outer={g.get_outer().get_name()}")
except Exception as e:
    print(f"  ERR: {e}")

# 2. BlueprintEditorLibrary.find_graph로 주요 이름 시도
sep("BlueprintEditorLibrary.find_graph")
for gn in ("IK", "AnimGraph", "EventGraph", "IsProne"):
    try:
        g = bel.find_graph(asset, gn)
        if g:
            nodes = list(g.get_editor_property("nodes") or [])
            print(f"  ✓ '{gn}' → {g.get_name()} (nodes={len(nodes)})")
        else:
            print(f"  ✗ '{gn}' → None")
    except Exception as e:
        print(f"  ✗ '{gn}' → ERR {str(e)[:80]}")

# 3. 주요 그래프 안의 노드 전수 덤프
def dump_graph(g, label):
    sep(f"그래프 '{label}' 노드 상세")
    try:
        nodes = list(g.get_editor_property("nodes") or [])
    except Exception as e:
        print(f"  nodes 읽기 err: {e}")
        return
    for n in nodes:
        cls = n.get_class().get_name()
        # variable_reference 확인
        vname = ""
        try:
            vref = n.get_editor_property("variable_reference")
            if vref:
                vname = str(vref.get_member_name())
        except Exception:
            pass
        keep = any(k in cls for k in ("FootPlacement", "VariableGet", "FunctionEntry",
                                        "FunctionResult", "Select", "BlendList", "IfThenElse")) \
               or ("Pelvis" in vname)
        if keep:
            name = n.get_name()
            print(f"  [{cls}] {name}" + (f"  var={vname}" if vname else ""))

# 시도 1: find_graph로 IK
ik_graph = None
try:
    ik_graph = bel.find_graph(asset, "IK")
except Exception:
    pass

if ik_graph:
    dump_graph(ik_graph, "IK")

# 시도 2: 전체 애니 그래프 전수 덤프
try:
    ag = list(asset.get_animation_graphs() or [])
    for g in ag:
        dump_graph(g, g.get_name())
except Exception:
    pass

# 4. FootPlacement 노드 직접 경로 접근 + PelvisSettings 값
sep("FootPlacement 노드 직접 접근 (find_object)")
paths = [
    f"{LAYER_PATH}.{asset.get_name()}:IK.AnimGraphNode_FootPlacement_0",
    f"{LAYER_PATH}.{asset.get_name()}:AnimGraph.AnimGraphNode_FootPlacement_0",
]
fp_node = None
for p in paths:
    try:
        n = unreal.find_object(None, p)
        if n:
            fp_node = n
            print(f"  ✓ FOUND: {p}")
            print(f"    class = {n.get_class().get_name()}")
            break
        else:
            print(f"  ✗ not found: {p}")
    except Exception as e:
        print(f"  ✗ err: {str(e)[:100]}")

if fp_node:
    # PelvisSettings 값
    try:
        anim_node = fp_node.get_editor_property("node")
        if anim_node:
            ps = anim_node.get_editor_property("pelvis_settings")
            if ps:
                print("\n  PelvisSettings (노드 default):")
                for fld in ("max_offset", "linear_stiffness", "pelvis_height_mode",
                            "horizontal_rebalancing_weight", "heel_lift_ratio"):
                    try:
                        print(f"    {fld} = {ps.get_editor_property(fld)}")
                    except Exception as e:
                        print(f"    {fld} = ERR {str(e)[:60]}")
    except Exception as e:
        print(f"  anim_node err: {e}")

    # 핀 상태
    try:
        pins = list(fp_node.get_editor_property("pins") or [])
        print(f"\n  핀 총 {len(pins)}개, PelvisSettings/PlantSettings/InterpolationSettings 핀:")
        for p in pins:
            try:
                pname = str(p.get_editor_property("pin_name"))
            except Exception:
                continue
            if any(k in pname for k in ("Pelvis", "PlantSettings", "InterpolationSettings")):
                direction = p.get_editor_property("direction")
                hidden = p.get_editor_property("b_hidden") if hasattr(p, "get_editor_property") else "?"
                linked = p.get_editor_property("linked_to") or []
                print(f"    {pname}: dir={direction} hidden={hidden} linked={len(linked)}")
                for lp in linked:
                    try:
                        on = lp.get_owning_node()
                        on_cls = on.get_class().get_name()
                        lp_name = str(lp.get_editor_property("pin_name"))
                        # 연결된 노드가 VariableGet이면 변수 이름도
                        extra = ""
                        try:
                            vref = on.get_editor_property("variable_reference")
                            if vref:
                                extra = f" var={vref.get_member_name()}"
                        except Exception:
                            pass
                        print(f"      <- {on_cls} ({on.get_name()}).{lp_name}{extra}")
                    except Exception as e:
                        print(f"      <- (err: {str(e)[:80]})")
    except Exception as e:
        print(f"  pin err: {e}")

print("\n[DONE]")
