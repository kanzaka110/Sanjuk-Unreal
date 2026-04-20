"""
PC_01_AnimLayer_IK의 FootPlacement 노드 파라미터 실측 덤프.
실행: UE 에디터 > Window > Developer Tools > Output Log > Cmd 드롭다운에서 'Python' 선택 후
  exec(open(r'C:/Dev/Sanjuk-Unreal/scripts/dump_footplacement_params.py').read())
"""

import unreal

LAYER_PATH = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK"


def section(title: str) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def dump_struct(label: str, struct) -> None:
    """UPROPERTY 스트럭트를 key=value로 펼쳐 출력."""
    print(f"\n[{label}]")
    if struct is None:
        print("  (None)")
        return
    try:
        props = struct.export_text()
        print("  " + props.replace(",", "\n  "))
    except Exception:
        for field in dir(struct):
            if field.startswith("_"):
                continue
            try:
                v = struct.get_editor_property(field)
                print(f"  {field} = {v}")
            except Exception:
                pass


def find_footplacement_nodes(asset):
    """AnimBlueprint의 모든 그래프 순회해서 FootPlacement 노드 수집."""
    results = []
    try:
        # Blueprint 그래프 순회 — UAnimBlueprint는 ubergraph + function graphs + anim graphs
        all_graphs = []
        try:
            all_graphs += list(asset.ubergraph_pages)
        except Exception:
            pass
        try:
            all_graphs += list(asset.function_graphs)
        except Exception:
            pass
        try:
            all_graphs += list(asset.anim_graph_pages or [])
        except Exception:
            pass

        for g in all_graphs:
            try:
                gname = g.get_name()
            except Exception:
                gname = "?"
            try:
                nodes = list(g.get_editor_property("nodes") or [])
            except Exception:
                nodes = []
            for n in nodes:
                cls = n.get_class().get_name()
                if "FootPlacement" in cls:
                    results.append((gname, n))
    except Exception as e:
        print(f"[ERR] graph enumerate: {e}")
    return results


def dump_node_property(node, name: str) -> None:
    try:
        v = node.get_editor_property(name)
        print(f"  {name} = {v}")
    except Exception as e:
        print(f"  {name} = (err: {e})")


asset = unreal.load_asset(LAYER_PATH)
if not asset:
    print(f"[ERR] load failed: {LAYER_PATH}")
else:
    section(f"에셋: {asset.get_name()}")
    print(f"Class  : {asset.get_class().get_name()}")
    try:
        print(f"Parent : {asset.get_editor_property('parent_class')}")
    except Exception:
        pass

    # 모든 FootPlacement 노드 찾기
    nodes = find_footplacement_nodes(asset)
    section(f"FootPlacement 노드 발견: {len(nodes)}개")
    for idx, (gname, node) in enumerate(nodes):
        print(f"\n--- [{idx}] graph='{gname}' class={node.get_class().get_name()} ---")

        # Runtime Node 속성 꺼내기 (AnimGraphNode → Node)
        runtime = None
        for key in ("node", "anim_node", "foot_placement_node"):
            try:
                runtime = node.get_editor_property(key)
                if runtime is not None:
                    break
            except Exception:
                continue

        if runtime is None:
            # 직접 top-level UPROPERTY 덤프
            for p in ("pelvis_settings", "plant_settings", "interpolation_settings",
                      "trace_settings", "ik_foot_root_bone", "pelvis_bone",
                      "leg_definitions", "plant_speed_mode"):
                dump_node_property(node, p)
        else:
            print(f"Runtime node class: {runtime.get_class().get_name()}")
            for p in ("pelvis_settings", "plant_settings", "interpolation_settings",
                      "trace_settings", "ik_foot_root_bone", "pelvis_bone",
                      "leg_definitions", "plant_speed_mode"):
                try:
                    v = runtime.get_editor_property(p)
                    if hasattr(v, "export_text"):
                        print(f"\n[{p}]")
                        print("  " + v.export_text().replace(",", "\n  "))
                    else:
                        print(f"{p} = {v}")
                except Exception as e:
                    print(f"{p} = (err: {str(e)[:60]})")

print("\n[DONE]")
