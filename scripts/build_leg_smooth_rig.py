"""
PC_01_CtrlRig_LegSmooth 빌드 스크립트

LegIK 출력 본의 temporal low-pass smoothing.
thigh_l/r, calf_l/r, foot_l/r 의 frame-to-frame 변동을 댐핑.

알고리즘 (per bone):
  smoothed = Lerp(prev_smoothed, current_pose, SmoothAlpha)
  prev_smoothed = smoothed  (다음 프레임용 BP 변수에 저장)

SmoothAlpha 범위:
  0.1 = 아주 강한 스무딩 (10% 현재 + 90% 이전) — 뜨거운 이불 효과, lag 큼
  0.3 = 권장 시작값 — tremor 효과적 댐핑 + lag 체감 적음
  0.5 = 약한 스무딩 (빠른 반응)
  1.0 = 스무딩 없음 (bypass)

실행:
  UE 에디터 Output Log Python 모드:
  exec(open("C:/Dev/Sanjuk-Unreal/scripts/build_leg_smooth_rig.py", encoding="utf-8").read())

AnimGraph 연결:
  PC_01_AnimLayer_IK IK 함수에서
    FootPlacement → LegIK (Alpha=1) → [ControlRig: LegSmooth] → FootClamp → Output

롤백:
  에셋 삭제 + AnimLayer_IK에서 ControlRig 노드 제거 → 원상복구.
"""
import unreal

ASSET_PATH = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_LegSmooth"
SOURCE_RIG = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_FootClamp"

BONES = ["thigh_l", "calf_l", "foot_l", "thigh_r", "calf_r", "foot_r"]
ALPHA_DEFAULT = "0.300000"

STRUCT_GET = "/Script/ControlRig.RigUnit_GetTransform"
STRUCT_SET = "/Script/ControlRig.RigUnit_SetTransform"
STRUCT_LERP = "/Script/RigVM.RigVMFunction_MathTransformLerp"
# Fallback struct paths if primary fails
STRUCT_LERP_ALT = [
    "/Script/ControlRig.RigVMFunction_MathTransformLerp",
    "/Script/RigVM.RigUnit_MathTransformLerp",
    "/Script/ControlRig.RigUnit_MathTransformLerp",
]


def log(msg): unreal.log(f"[LegSmooth] {msg}")
def err(msg): unreal.log_error(f"[LegSmooth] {msg}")


def main():
    eal = unreal.EditorAssetLibrary

    # 1) 에셋 생성/로드
    if not eal.does_asset_exist(ASSET_PATH):
        log(f"Duplicating from {SOURCE_RIG}")
        if not eal.duplicate_asset(SOURCE_RIG, ASSET_PATH):
            err("Duplicate failed")
            return
    else:
        log(f"Using existing asset {ASSET_PATH}")

    rig_bp = eal.load_asset(ASSET_PATH)
    if rig_bp is None:
        err("Load failed"); return

    try:
        controller = rig_bp.get_controller_by_name("RigVMModel")
    except Exception as e:
        err(f"get_controller: {e}"); return
    if controller is None:
        err("Controller None"); return

    # 2) BeginExecution 제외 모든 노드 삭제
    graph = controller.get_graph()
    begin_path = None
    removed = 0
    for node in list(graph.get_nodes()):
        np = node.get_node_path()
        if "BeginExecution" in np:
            begin_path = np
            continue
        try:
            controller.remove_node_by_name(np)
            removed += 1
        except Exception as e:
            err(f"remove_node {np}: {e}")
    log(f"Removed {removed} nodes, kept '{begin_path}'")

    if not begin_path:
        err("BeginExecution not found")
        return

    # 3) BP 멤버 변수 추가 (persistent state across frames)
    # 기존 변수 제거 후 재생성 (idempotent)
    existing_vars = []
    try:
        for v in rig_bp.get_public_variables():
            existing_vars.append(v.name)
    except Exception:
        pass
    log(f"Existing vars: {existing_vars}")

    # Prev_<bone> (FTransform) × 6
    for bone in BONES:
        vname = f"Prev_{bone}"
        if vname in existing_vars:
            continue
        # Try multiple API forms
        ok = False
        for attempt in [
            lambda: rig_bp.add_member_variable(vname, "FTransform", False, False, ""),
            lambda: unreal.BlueprintEditorLibrary.add_member_variable(rig_bp, vname, "FTransform", "", ""),
        ]:
            try:
                attempt()
                ok = True
                log(f"Added var {vname}")
                break
            except Exception as e:
                err(f"var {vname} attempt: {e}")
        if not ok:
            err(f"All attempts failed for {vname}")

    # SmoothAlpha (float)
    if "SmoothAlpha" not in existing_vars:
        ok = False
        for attempt in [
            lambda: rig_bp.add_member_variable("SmoothAlpha", "float", True, False, ALPHA_DEFAULT),
            lambda: unreal.BlueprintEditorLibrary.add_member_variable(rig_bp, "SmoothAlpha", "float", "", ALPHA_DEFAULT),
        ]:
            try:
                attempt()
                ok = True
                log(f"Added SmoothAlpha = {ALPHA_DEFAULT}")
                break
            except Exception as e:
                err(f"SmoothAlpha attempt: {e}")

    # 4) Lerp struct 경로 결정 (fallback 탐색)
    def try_add_unit(path, name, x, y):
        try:
            n = controller.add_unit_node_from_struct_path(
                path, "Execute", unreal.Vector2D(x, y), name
            )
            return n is not None
        except Exception as e:
            return False

    lerp_path = None
    for p in [STRUCT_LERP] + STRUCT_LERP_ALT:
        if try_add_unit(p, "_probe_lerp", -1000, -1000):
            lerp_path = p
            controller.remove_node_by_name("_probe_lerp")
            break
    if lerp_path is None:
        err("No working Lerp struct found — aborting")
        return
    log(f"Using Lerp: {lerp_path}")

    # 5) 노드 추가
    def add_unit(path, name, x, y):
        try:
            controller.add_unit_node_from_struct_path(
                path, "Execute", unreal.Vector2D(x, y), name
            )
            log(f"Added {name} ({path.split('.')[-1]})")
        except Exception as e:
            err(f"add_unit {name}: {e}")

    def add_var(name, var_name, cpp_type, is_getter, x, y):
        try:
            controller.add_variable_node(
                var_name, cpp_type, "", is_getter, "", unreal.Vector2D(x, y), name
            )
            log(f"Added {'Get' if is_getter else 'Set'} {name} → {var_name}")
        except Exception as e:
            err(f"add_var {name}: {e}")

    # Alpha getter (공유)
    add_var("AlphaGet", "SmoothAlpha", "float", True, 200, 0)

    # Per-bone nodes
    for i, bone in enumerate(BONES):
        y = 300 + i * 700
        add_unit(STRUCT_GET, f"Get_{bone}", 400, y)
        add_var(f"PrevGet_{bone}", f"Prev_{bone}", "FTransform", True, 400, y + 200)
        add_unit(lerp_path, f"Lerp_{bone}", 800, y + 100)
        add_unit(STRUCT_SET, f"Set_{bone}", 1200, y)
        add_var(f"PrevSet_{bone}", f"Prev_{bone}", "FTransform", False, 1600, y + 50)

    # 6) 핀 기본값
    def set_pin(pp, v):
        try:
            controller.set_pin_default_value(pp, v, False)
        except Exception as e:
            err(f"set_pin {pp}={v}: {e}")

    for bone in BONES:
        set_pin(f"Get_{bone}.Item.Type", "Bone")
        set_pin(f"Get_{bone}.Item.Name", bone)
        set_pin(f"Get_{bone}.Space", "GlobalSpace")
        set_pin(f"Set_{bone}.Item.Type", "Bone")
        set_pin(f"Set_{bone}.Item.Name", bone)
        set_pin(f"Set_{bone}.Space", "GlobalSpace")
        set_pin(f"Set_{bone}.Weight", "1.000000")
        set_pin(f"Set_{bone}.bPropagateToChildren", "False")
        set_pin(f"Set_{bone}.bInitial", "False")

    # 7) 링크
    def link(src, tgt):
        try:
            controller.add_link(src, tgt)
        except Exception as e:
            err(f"link {src} -> {tgt}: {e}")

    for bone in BONES:
        # Lerp: A=Prev, B=Current, T=Alpha
        link(f"PrevGet_{bone}.Value", f"Lerp_{bone}.A")
        link(f"Get_{bone}.Transform", f"Lerp_{bone}.B")
        link("AlphaGet.Value", f"Lerp_{bone}.T")
        # Lerp → SetTransform.Value + PrevSet.Value
        link(f"Lerp_{bone}.Result", f"Set_{bone}.Value")
        link(f"Lerp_{bone}.Result", f"PrevSet_{bone}.Value")

    # Execution chain: Begin → Set_b1 → PrevSet_b1 → Set_b2 → PrevSet_b2 → ...
    prev_exec = f"{begin_path}.ExecutePin"
    for bone in BONES:
        link(prev_exec, f"Set_{bone}.ExecutePin")
        link(f"Set_{bone}.ExecutePin", f"PrevSet_{bone}.ExecutePin")
        prev_exec = f"PrevSet_{bone}.ExecutePin"

    # 8) Compile + Save
    try:
        unreal.BlueprintEditorLibrary.compile_blueprint(rig_bp)
        log("Compiled")
    except Exception as e:
        err(f"Compile: {e}")

    try:
        eal.save_asset(ASSET_PATH)
        log("Saved")
    except Exception as e:
        err(f"Save: {e}")

    log("=" * 60)
    log("Done. Next:")
    log(f"  Open PC_01_AnimLayer_IK → IK function graph")
    log(f"  Add 'Control Rig' anim node → Class = PC_01_CtrlRig_LegSmooth")
    log(f"  Insert in chain: LegIK → [THIS] → FootClamp")
    log(f"  Compile + Save the AnimLayer")
    log(f"  Tweak SmoothAlpha (class default): 0.3 (default) → 0.1 more damping / 0.5 less")


main()
