import unreal

LAYER_PATH = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK"

def section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def safe(fn):
    try:
        return fn()
    except Exception as e:
        return "(err: " + str(e)[:80] + ")"

asset = unreal.load_asset(LAYER_PATH)
if not asset:
    print("[ERROR] Failed to load: " + LAYER_PATH)
    raise SystemExit

section("기본 정보")
print("Name  : " + asset.get_name())
print("Class : " + asset.get_class().get_name())
print("Skel  : " + safe(lambda: asset.get_editor_property("target_skeleton").get_path_name()))
print("Parent: " + safe(lambda: str(asset.get_editor_property("parent_class"))))

section("Asset Registry: 의존성")
ar = unreal.AssetRegistryHelpers.get_asset_registry()
opts = unreal.AssetRegistryDependencyOptions(include_hard_package_references=True)
deps = list(ar.get_dependencies(unreal.Name(LAYER_PATH), opts) or [])
print("[총 " + str(len(deps)) + "개]")
for d in deps:
    print("  - " + str(d))

section("Asset Registry: 사용처(Referencers)")
refs = list(ar.get_referencers(unreal.Name(LAYER_PATH), opts) or [])
print("[총 " + str(len(refs)) + "개]")
for r in refs:
    print("  - " + str(r))

section("패키지 내부 객체 스캔 (AnimGraph 노드 추정)")
package = asset.get_outermost()
KEYWORDS = ["AnimGraphNode", "AnimNode", "ControlRig", "TwoBoneIK",
            "FullBodyIK", "FBIK", "FootIK", "BasicFootIK", "ApplyAdditive",
            "BlendListByEnum", "Layered", "Slot", "BoneDriven",
            "ModifyBone", "CopyBone", "RotateBone", "Transition",
            "Sequence", "BlendSpace", "StateMachine", "LinkedAnim",
            "InputPose", "OutputPose", "PoseDriver", "Aim", "LookAt"]

found_classes = {}
try:
    inner = unreal.find_objects_with_outer(package)
    print("Inner objects: " + str(len(inner)))
    for obj in inner:
        cls_name = obj.get_class().get_name()
        if any(kw.lower() in cls_name.lower() for kw in KEYWORDS):
            found_classes.setdefault(cls_name, []).append(obj.get_name())
except Exception as e:
    print("inner enumerate err: " + str(e)[:120])

if found_classes:
    print("\n[Anim 관련 노드/객체 분류]")
    for cls in sorted(found_classes.keys()):
        names = found_classes[cls]
        print("  " + cls + " x " + str(len(names)))
        for n in names[:6]:
            print("    - " + n)
        if len(names) > 6:
            print("    ... (+" + str(len(names) - 6) + ")")
else:
    print("(분류된 노드 없음 — find_objects_with_outer 실패 가능)")

section("바이너리 스캔 보조 (이 스크립트로는 한계가 있어 grep으로 보조)")
print("아래 명령으로 추가 정보 가능:")
print('  tr -c "[:print:]\\n" "\\n" < ' +
      '"<asset path>.uasset" | grep AnimGraphNode | sort -u')

print("\n[DONE]")
