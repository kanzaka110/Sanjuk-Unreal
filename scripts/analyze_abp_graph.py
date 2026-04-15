import unreal

ABP_PATH = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"

def section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def safe(fn, default="(unavailable)"):
    try:
        return fn()
    except Exception as e:
        return "(err: " + str(e)[:80] + ")"

abp = unreal.load_asset(ABP_PATH)
if not abp:
    print("[ERROR] Failed to load ABP")
    raise SystemExit

section("생성 클래스 (AnimBlueprintGeneratedClass)")
gen_class = safe(lambda: abp.get_editor_property("generated_class"))
print("GeneratedClass : " + str(gen_class))

section("AnimBP 주요 프로퍼티 스캔")
PROPS = [
    "animation_graph", "anim_graph", "anim_node_properties",
    "state_machines", "linked_anim_graph_node_properties",
    "ubergraph_pages", "function_graphs", "macro_graphs",
    "delegate_graphs", "intermediate_graphs",
    "event_graphs", "implemented_graphs",
    "blueprint_category", "blueprint_type",
    "preview_skeletal_mesh", "preview_animation_blueprint",
]
for p in PROPS:
    try:
        val = abp.get_editor_property(p)
        if val is not None:
            if hasattr(val, "__len__"):
                print("- " + p + " : [" + str(len(val)) + " items]")
                for i, item in enumerate(list(val)[:10]):
                    print("    [" + str(i) + "] " + str(item))
            else:
                print("- " + p + " : " + str(val))
    except Exception:
        pass

section("BlueprintEditorLibrary: 모든 그래프 열거")
try:
    bel = unreal.BlueprintEditorLibrary
    graphs = bel.get_all_graphs(abp)
    if graphs:
        for g in graphs:
            gname = safe(lambda g=g: g.get_name())
            print("- " + gname)
            try:
                nodes = bel.get_nodes(g)
                for n in nodes[:20]:
                    nname = safe(lambda n=n: n.get_name())
                    ncls = safe(lambda n=n: n.get_class().get_name())
                    print("    · " + ncls + " [" + nname + "]")
                if len(nodes) > 20:
                    print("    ... (+" + str(len(nodes) - 20) + " more)")
            except Exception as e:
                print("    (nodes err: " + str(e)[:60] + ")")
    else:
        print("(그래프 조회 결과 없음)")
except AttributeError:
    print("BlueprintEditorLibrary.get_all_graphs 미지원 (구 버전)")
except Exception as e:
    print("(err: " + str(e)[:120] + ")")

section("클래스 내부 애니메이션 관련 프로퍼티")
if gen_class:
    CLASS_PROPS = [
        "anim_node_properties", "linked_anim_graph_node_properties",
        "state_machines", "exposed_value_handler_index",
        "sub_instance_property_name", "ordered_saved_pose_indices_map",
    ]
    for p in CLASS_PROPS:
        try:
            val = gen_class.get_editor_property(p)
            if val is not None:
                if hasattr(val, "__len__"):
                    print("- " + p + " : [" + str(len(val)) + " items]")
                else:
                    print("- " + p + " : " + str(val))
        except Exception:
            pass

section("Anim 관련 에셋 (재참조로부터 추정 그래프 사용처)")
RELEVANT_REFS = {
    "StateMachine": "/Game/ART/Character/PC/PC_01/StateMachine/",
    "MotionMatching": "/Game/ART/Character/PC/PC_01/MotionMatching/",
    "OverlaySystem": "/Game/ART/Character/PC/PC_01/OverlaySystem/",
    "TravelSystem": "/Game/ART/Character/PC/PC_01/TravelSystem/",
    "Animation": "/Game/ART/Character/PC/PC_01/Animation/",
}
ar = unreal.AssetRegistryHelpers.get_asset_registry()
for label, path in RELEVANT_REFS.items():
    try:
        assets = ar.get_assets_by_path(unreal.Name(path), recursive=True)
        if assets:
            print("\n[" + label + "] " + path)
            for a in list(assets)[:15]:
                n = str(a.asset_name) + " (" + str(a.asset_class_path.asset_name) + ")"
                print("  - " + n)
            if len(list(assets)) > 15:
                print("  ... (+" + str(len(list(assets)) - 15) + " more)")
    except Exception as e:
        print(label + ": err " + str(e)[:60])

print("\n[DONE]")
