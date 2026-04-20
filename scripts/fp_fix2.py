"""FootPlacement 기본값 복귀 — 슬로프 해결은 유지, 계단 과민반응 제거."""
import unreal

LAYER_PATH = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK"
NODE_PATH = f"{LAYER_PATH}.PC_01_AnimLayer_IK:IK.AnimGraphNode_FootPlacement_0"

# 슬로프 해결을 위한 최소 변경 + UE 기본값 복귀
PELVIS_TARGET = {
    "max_offset": 30.0,
    "linear_stiffness": 350.0,                 # UE 기본 (기존 300 → 복귀)
    "linear_damping": 1.0,                     # UE 기본
    "horizontal_rebalancing_weight": 0.3,      # UE 기본 (기존 0.5 → 복귀)
    "max_offset_horizontal": 10.0,             # UE 기본
    "heel_lift_ratio": 0.5,                    # UE 기본 (기존 0.7 → 복귀)
    "pelvis_height_mode": unreal.PelvisHeightMode.FRONT_PLANTED_FEET_UPHILL_FRONT_FEET_DOWNHILL,
    "actor_movement_compensation_mode": unreal.ActorMovementCompensationMode.SUDDEN_MOTION_ONLY,
}

TRACE_TARGET = {
    "start_offset": -75.0,                     # UE 기본 (기존 -30/-60 → 복귀)
    "end_offset": 70.0,
    "sweep_radius": 5.0,                       # UE 기본 (기존 2 → 복귀)
    "max_ground_penetration": 20.0,            # 기존 유지 (10 → 20)
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

anim_node = fp.get_editor_property("node")

# ==== PelvisSettings ====
sep("현재 PelvisSettings")
ps = anim_node.get_editor_property("pelvis_settings")
for k in PELVIS_TARGET:
    try:
        print(f"  {k:40s} = {ps.get_editor_property(k)}")
    except Exception:
        pass

sep("PelvisSettings 쓰기")
fp.modify()
pelvis_fail = []
for k, v in PELVIS_TARGET.items():
    try:
        ps.set_editor_property(k, v)
        print(f"  ✓ {k:40s} → {v}")
    except Exception as e:
        pelvis_fail.append((k, str(e)[:80]))
        print(f"  ✗ {k:40s} {str(e)[:80]}")

anim_node.set_editor_property("pelvis_settings", ps)

# ==== TraceSettings ====
sep("현재 TraceSettings")
ts = anim_node.get_editor_property("trace_settings")
for k in TRACE_TARGET:
    try:
        print(f"  {k:40s} = {ts.get_editor_property(k)}")
    except Exception:
        pass

sep("TraceSettings 쓰기")
trace_fail = []
for k, v in TRACE_TARGET.items():
    try:
        ts.set_editor_property(k, v)
        print(f"  ✓ {k:40s} → {v}")
    except Exception as e:
        trace_fail.append((k, str(e)[:80]))
        print(f"  ✗ {k:40s} {str(e)[:80]}")

anim_node.set_editor_property("trace_settings", ts)
fp.set_editor_property("node", anim_node)

# ==== 검증 (in-memory) ====
sep("검증 (쓴 후 다시 읽기)")
ps2 = anim_node.get_editor_property("pelvis_settings")
ts2 = anim_node.get_editor_property("trace_settings")
print("PelvisSettings:")
for k, want in PELVIS_TARGET.items():
    try:
        v = ps2.get_editor_property(k)
        m = "✓" if v == want else "✗"
        print(f"  {m} {k:40s} = {v}")
    except Exception:
        pass
print("TraceSettings:")
for k, want in TRACE_TARGET.items():
    try:
        v = ts2.get_editor_property(k)
        m = "✓" if v == want else "✗"
        print(f"  {m} {k:40s} = {v}")
    except Exception:
        pass

# ==== 컴파일 + 저장 ====
sep("컴파일 + 저장")
bel = unreal.BlueprintEditorLibrary
try:
    bel.compile_blueprint(asset)
    print("  ✓ compile_blueprint")
except Exception as e:
    print(f"  ✗ compile: {str(e)[:100]}")

# Mark dirty
try:
    asset.modify()
    unreal.EditorAssetLibrary.save_asset(LAYER_PATH)
    print("  ✓ save_asset")
except Exception as e:
    print(f"  ✗ save: {str(e)[:100]}")

print(f"\n[DONE] pelvis_fail={len(pelvis_fail)}, trace_fail={len(trace_fail)}")
if pelvis_fail or trace_fail:
    for k, e in pelvis_fail + trace_fail:
        print(f"  FAIL {k}: {e}")

print("\n⚠️  PIE가 켜져 있으면 Stop 후 다시 Play하세요. 변경사항은 PIE 재시작 시만 반영됩니다.")
