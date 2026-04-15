import unreal

RIG_PATH = "/Game/ART/Character/PC/PC_01/Rig/PC_01_CtrlRig_FootClamp"

def section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def safe(fn, default=""):
    try:
        return fn()
    except Exception as e:
        return "(err: " + str(e)[:80] + ")"

asset = unreal.load_asset(RIG_PATH)
if not asset:
    print("[ERROR] Failed to load")
    raise SystemExit

section("Controller / Graph 접근 시도")
controller = None
graph = None
try:
    controller = asset.get_controller_by_name("RigVMModel")
    print("Controller (RigVMModel): " + str(controller))
except Exception as e:
    print("get_controller_by_name err: " + str(e)[:100])

if not controller:
    try:
        controller = asset.get_local_function_library_controller()
        print("Controller (LocalFnLib): " + str(controller))
    except Exception as e:
        print("local_fn_lib err: " + str(e)[:100])

# Try common controller methods
if controller:
    try:
        graph = controller.get_graph()
        print("Graph: " + str(graph))
    except Exception as e:
        print("get_graph err: " + str(e)[:100])

# Try direct access
try:
    rig_graph = asset.get_editor_property("rig_graph")
    print("rig_graph: " + str(rig_graph))
except Exception:
    pass

try:
    func_lib = asset.get_editor_property("local_function_library")
    print("local_function_library: " + str(func_lib))
except Exception:
    pass

section("패키지 내 모든 객체 열거")
package = asset.get_outermost()
print("Package: " + package.get_name())

try:
    inner = unreal.find_objects_with_outer(package)
    print("Inner objects: " + str(len(inner)))
except Exception:
    inner = []

if not inner:
    # Fallback: iterate via known reflection
    try:
        from typing import List
        objs = unreal.SystemLibrary.get_object_class(asset)
        print("Fallback class probe: " + str(objs))
    except Exception:
        pass

# Print classes of interest
section("RigVM / Control Rig 노드 클래스 필터")
KEYWORDS = ["RigUnit", "RigVMNode", "RigVMUnit", "DispatchNode",
            "ControlRig", "FullBody", "TwoBone", "BasicIK", "Aim",
            "Distribute", "Project", "Set", "Get", "FootIK", "Foot",
            "Solve", "Limit", "Constraint"]

found = []
for obj in inner:
    cls_name = obj.get_class().get_name()
    if any(kw.lower() in cls_name.lower() for kw in KEYWORDS):
        found.append((cls_name, obj.get_name()))

print("Found " + str(len(found)) + " candidate nodes/units:")
for cls, name in found[:80]:
    print("  - " + cls + " :: " + name)

section("Hierarchy (본 / 컨트롤)")
try:
    hier = asset.get_editor_property("hierarchy")
    if hier:
        # Try getting all elements
        for method in ["get_keys", "get_elements", "get_all_keys",
                       "get_bone_keys", "get_control_keys"]:
            try:
                fn = getattr(hier, method, None)
                if fn:
                    items = fn()
                    print("\n[" + method + "] (" + str(len(items)) + ")")
                    for it in list(items)[:30]:
                        print("  - " + str(it))
            except Exception as e:
                pass
except Exception as e:
    print("hierarchy err: " + str(e)[:100])

print("\n[DONE]")
