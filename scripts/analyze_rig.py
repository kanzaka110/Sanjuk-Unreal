import unreal

RIG_PATH = "/Game/ART/Character/PC/PC_01/Rig/PC_01_CtrlRig_FootClamp"

def section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def safe(fn):
    try:
        return fn()
    except Exception as e:
        return "(err: " + str(e)[:80] + ")"

asset = unreal.load_asset(RIG_PATH)
if not asset:
    print("[ERROR] Failed to load: " + RIG_PATH)
    raise SystemExit

section("기본 정보")
print("Name  : " + asset.get_name())
print("Class : " + asset.get_class().get_name())
print("Path  : " + asset.get_path_name())

section("주요 프로퍼티 스캔")
PROPS = [
    "preview_skeletal_mesh", "source_hierarchy_import",
    "shapes", "controller", "hierarchy", "construction_event_chain",
    "forwards_solve_event_chain", "backwards_solve_event_chain",
    "user_defined_event_names",
    "exposed_pins_to_blueprint", "function_graphs",
    "vm_runtime", "rig_graph_display_settings",
    "rig_modules", "rig_module_settings",
]
for p in PROPS:
    try:
        val = asset.get_editor_property(p)
        if val is not None:
            if hasattr(val, "__len__") and not isinstance(val, str):
                ln = len(val)
                print("- " + p + " : [" + str(ln) + " items]")
                for i, item in enumerate(list(val)[:8]):
                    print("    [" + str(i) + "] " + str(item)[:120])
            else:
                print("- " + p + " : " + str(val)[:120])
    except Exception:
        pass

section("Hierarchy (Bones / Controls / Nulls)")
try:
    hier = asset.get_hierarchy()
    if hier:
        print("Hierarchy obj : " + str(hier))
        # Try common API
        for method in ["get_bones", "get_controls", "get_nulls", "get_curves"]:
            try:
                fn = getattr(hier, method)
                items = fn()
                print("\n[" + method + "] (" + str(len(items)) + ")")
                for it in list(items)[:20]:
                    print("  - " + str(it))
            except Exception as e:
                print("[" + method + "] err: " + str(e)[:60])
except Exception as e:
    print("Hierarchy access err: " + str(e)[:120])

section("Asset Registry: 의존/참조")
ar = unreal.AssetRegistryHelpers.get_asset_registry()
opts = unreal.AssetRegistryDependencyOptions(include_hard_package_references=True)
deps = ar.get_dependencies(unreal.Name(RIG_PATH), opts) or []
print("[Dependencies] " + str(len(list(deps))))
for d in list(deps)[:30]:
    print("  - " + str(d))

refs = ar.get_referencers(unreal.Name(RIG_PATH), opts) or []
print("\n[Referencers] " + str(len(list(refs))))
for r in list(refs)[:20]:
    print("  - " + str(r))

section("BlueprintEditorLibrary 그래프 / 노드")
try:
    bel = unreal.BlueprintEditorLibrary
    graphs = bel.get_all_graphs(asset)
    if graphs:
        for g in graphs:
            gn = safe(lambda g=g: g.get_name())
            print("\n[Graph] " + gn)
            try:
                nodes = bel.get_nodes(g)
                for n in nodes[:25]:
                    nname = safe(lambda n=n: n.get_name())
                    ncls = safe(lambda n=n: n.get_class().get_name())
                    print("  · " + ncls + " [" + nname + "]")
                if len(nodes) > 25:
                    print("  ... (+" + str(len(nodes) - 25) + ")")
            except Exception as e:
                print("  (nodes err: " + str(e)[:60] + ")")
except Exception as e:
    print("(BEL err: " + str(e)[:120] + ")")

print("\n[DONE]")
