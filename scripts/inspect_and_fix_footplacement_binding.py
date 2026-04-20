"""
PC_01_AnimLayer_IK의 FootPlacement 노드 PelvisSettings 바인딩 상태 진단 + 복원 시도.

실행: UE 에디터 Output Log > Cmd 드롭다운에서 'Python' 선택 후
  exec(open(r'C:/Dev/Sanjuk-Unreal/scripts/inspect_and_fix_footplacement_binding.py').read())
"""

import unreal

LAYER_PATH = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK"


def sep(title: str) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def dump_struct(label: str, s) -> None:
    print(f"  [{label}]")
    if s is None:
        print("    (None)")
        return
    try:
        for field in ("max_offset", "linear_stiffness", "linear_damping",
                      "horizontal_rebalancing_weight", "heel_lift_ratio",
                      "pelvis_height_mode", "actor_movement_compensation_mode",
                      "b_enable_interpolation"):
            try:
                v = s.get_editor_property(field)
                print(f"    {field} = {v}")
            except Exception:
                pass
    except Exception as e:
        print(f"    (err: {e})")


asset = unreal.load_asset(LAYER_PATH)
if not asset:
    print(f"[ERR] asset load failed: {LAYER_PATH}")
    raise SystemExit

sep("Asset info")
print(f"  name = {asset.get_name()}")
print(f"  class = {asset.get_class().get_name()}")

# 1. 모든 그래프 순회
all_graphs = []
try:
    for g in asset.ubergraph_pages or []:
        all_graphs.append(("ubergraph", g))
except Exception:
    pass
try:
    for g in asset.function_graphs or []:
        all_graphs.append(("function", g))
except Exception:
    pass
# AnimBlueprint-specific
try:
    for g in asset.anim_graph_pages or []:
        all_graphs.append(("anim_graph", g))
except Exception:
    pass
try:
    for g in asset.interface_pages or []:
        all_graphs.append(("interface", g))
except Exception:
    pass

sep(f"Graphs found: {len(all_graphs)}")
for kind, g in all_graphs:
    try:
        gname = g.get_name()
    except Exception:
        gname = "?"
    try:
        nodes = list(g.get_editor_property("nodes") or [])
    except Exception:
        nodes = []
    print(f"  [{kind}] {gname} — {len(nodes)} nodes")

# 2. FootPlacement 노드 + PelvisSettings* 변수 Get 노드 찾기
sep("Node scan")
fp_nodes = []
pelvis_get_nodes = []
for kind, g in all_graphs:
    try:
        nodes = list(g.get_editor_property("nodes") or [])
    except Exception:
        continue
    for n in nodes:
        cls = n.get_class().get_name()
        try:
            ntitle = n.get_node_title(unreal.ENodeTitleType.FULL_TITLE_TYPE) if hasattr(n, 'get_node_title') else str(n)
        except Exception:
            ntitle = "?"
        if "FootPlacement" in cls:
            fp_nodes.append((kind, g, n))
            print(f"  [FP] graph={g.get_name()} class={cls}")
        if cls == "K2Node_VariableGet":
            try:
                var_ref = n.get_editor_property("variable_reference")
                var_name = var_ref.get_member_name() if var_ref else ""
            except Exception:
                var_name = ""
            if "Pelvis" in str(var_name):
                pelvis_get_nodes.append((kind, g, n, str(var_name)))
                print(f"  [GetVar] graph={g.get_name()} var={var_name}")

# 3. FootPlacement 노드의 PelvisSettings 핀 상태
sep("FootPlacement 노드 상세")
for idx, (kind, g, node) in enumerate(fp_nodes):
    print(f"\n  --- [{idx}] graph={g.get_name()} ---")
    # Get the animation node struct
    try:
        anim_node = node.get_editor_property("node")
        if anim_node is not None:
            print(f"    runtime node class: {anim_node.get_class().get_name()}")
            ps = None
            try:
                ps = anim_node.get_editor_property("pelvis_settings")
            except Exception:
                pass
            if ps is not None:
                dump_struct("PelvisSettings (node default)", ps)
    except Exception as e:
        print(f"    runtime fetch err: {e}")
    # Pin inspection
    try:
        pins = list(node.get_editor_property("pins") or [])
        print(f"    total pins: {len(pins)}")
        for p in pins:
            try:
                pname = p.pin_name if hasattr(p, 'pin_name') else p.get_editor_property('pin_name')
            except Exception:
                pname = "?"
            if "Pelvis" in str(pname) or "pelvis" in str(pname).lower():
                try:
                    direction = p.direction if hasattr(p, 'direction') else p.get_editor_property('direction')
                except Exception:
                    direction = "?"
                try:
                    linked_to = p.linked_to if hasattr(p, 'linked_to') else p.get_editor_property('linked_to')
                except Exception:
                    linked_to = []
                try:
                    hidden = p.b_hidden if hasattr(p, 'b_hidden') else p.get_editor_property('b_hidden')
                except Exception:
                    hidden = "?"
                print(f"    PIN: {pname} dir={direction} hidden={hidden} linked_count={len(linked_to) if linked_to else 0}")
    except Exception as e:
        print(f"    pin inspect err: {e}")

sep("PelvisSettings* 변수 Get 사용처")
if not pelvis_get_nodes:
    print("  (없음) — PelvisSettingsDefault/Prone 변수가 아무 그래프에서도 Get 되지 않고 있음!")
    print("  ➜ 바인딩 완전히 끊긴 상태. 복원 필요.")
else:
    for idx, (kind, g, n, vn) in enumerate(pelvis_get_nodes):
        print(f"  [{idx}] var={vn} graph={g.get_name()}")
        # Check what the output pin is connected to
        try:
            pins = list(n.get_editor_property("pins") or [])
            for p in pins:
                try:
                    pname = p.pin_name if hasattr(p, 'pin_name') else p.get_editor_property('pin_name')
                    direction = p.direction if hasattr(p, 'direction') else p.get_editor_property('direction')
                    linked_to = p.linked_to if hasattr(p, 'linked_to') else p.get_editor_property('linked_to')
                except Exception:
                    continue
                if str(direction) == "EGPD_Output" or "Output" in str(direction):
                    if linked_to:
                        for lp in linked_to:
                            try:
                                owner = lp.get_owning_node()
                                print(f"    → {owner.get_class().get_name()} ({owner.get_name()}).{lp.pin_name if hasattr(lp,'pin_name') else '?'}")
                            except Exception:
                                pass
                    else:
                        print(f"    → NO CONNECTION (output not used)")
        except Exception:
            pass

sep("진단 요약")
if not pelvis_get_nodes and fp_nodes:
    print("  ❌ PelvisSettingsDefault 변수가 어디에도 사용되지 않고 있음")
    print("  ❌ FootPlacement.PelvisSettings는 노드 default만 쓰는데 컴파일된 CDO는 struct 기본값")
    print("  → 변수에서 노드로 연결하는 작업 필요")
else:
    print("  ⚠️ 변수가 어딘가 사용 중. 연결 경로 확인 필요 (위 출력 참고)")

print("\n[DONE]")
