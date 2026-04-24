"""FootPlacement 노드 PelvisSettings를 PelvisSettingsDefault 값으로 복원."""
import unreal

LAYER_PATH = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK"
NODE_PATH = f"{LAYER_PATH}.PC_01_AnimLayer_IK:IK.AnimGraphNode_FootPlacement_0"

# PelvisSettingsDefault 변수의 값 (2026-04-20 CDO 덤프 실측)
TARGET = {
    "max_offset": 10.0,
    "linear_stiffness": 300.0,
    "linear_damping": 1.0,
    "horizontal_rebalancing_weight": 0.5,
    "max_offset_horizontal": 15.0,
    "heel_lift_ratio": 0.5,
    "pelvis_height_mode": unreal.PelvisHeightMode.FRONT_PLANTED_FEET_UPHILL_FRONT_FEET_DOWNHILL,
    "actor_movement_compensation_mode": unreal.ActorMovementCompensationMode.SUDDEN_MOTION_ONLY,
    "b_enable_interpolation": True,
    "b_disable_pelvis_offset_in_air": False,
}


def sep(s):
    print("\n" + "=" * 70)
    print(s)
    print("=" * 70)


asset = unreal.load_asset(LAYER_PATH)
fp = unreal.find_object(None, NODE_PATH)
if not fp:
    print(f"[ERR] FP node not found: {NODE_PATH}")
    raise SystemExit

sep("현재 값 읽기")
anim_node = fp.get_editor_property("node")
ps = anim_node.get_editor_property("pelvis_settings")

before = {}
for k in TARGET:
    try:
        before[k] = ps.get_editor_property(k)
        print(f"  {k:40s} = {before[k]}")
    except Exception as e:
        print(f"  {k:40s} = ERR {str(e)[:60]}")

sep("값 쓰기")
fp.modify()  # 트랜잭션 기록용
success, failed = [], []
for k, v in TARGET.items():
    try:
        ps.set_editor_property(k, v)
        success.append(k)
        print(f"  ✓ {k:40s} → {v}")
    except Exception as e:
        failed.append((k, str(e)[:80]))
        print(f"  ✗ {k:40s} ERR {str(e)[:80]}")

# 변경된 struct를 다시 anim_node에 세팅
sep("struct 재할당")
try:
    anim_node.set_editor_property("pelvis_settings", ps)
    print("  ✓ anim_node.pelvis_settings 재할당")
except Exception as e:
    print(f"  ✗ ERR {str(e)[:100]}")

# AnimGraphNode에도 반영 (일부 UE 버전은 여기도 저장)
try:
    fp.set_editor_property("node", anim_node)
    print("  ✓ fp.node 재할당")
except Exception as e:
    print(f"  ✗ fp.node ERR {str(e)[:100]}")

sep("검증 — 쓴 후 다시 읽기")
ps2 = anim_node.get_editor_property("pelvis_settings")
for k in TARGET:
    try:
        v = ps2.get_editor_property(k)
        matched = "✓" if v == TARGET[k] else "✗"
        print(f"  {matched} {k:40s} = {v}  (target={TARGET[k]})")
    except Exception as e:
        print(f"  ? {k:40s} err")

sep("컴파일 + 저장")
bel = unreal.BlueprintEditorLibrary
try:
    bel.compile_blueprint(asset)
    print("  ✓ compile_blueprint")
except Exception as e:
    print(f"  ✗ compile err {str(e)[:100]}")

try:
    unreal.EditorAssetLibrary.save_asset(LAYER_PATH)
    print("  ✓ save_asset")
except Exception as e:
    print(f"  ✗ save err {str(e)[:100]}")

print(f"\n[DONE] success={len(success)}, failed={len(failed)}")
if failed:
    for k, e in failed:
        print(f"  FAIL: {k}: {e}")
