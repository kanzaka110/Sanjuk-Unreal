"""
PC_01_CtrlRig_TwoBoneLegIK 빌드 스크립트
대상: UE 5.7.4 (SB2 커스텀)

실행 방법:
  UE 에디터 > Window > Developer Tools > Output Log
  하단 드롭다운을 'Python' 선택 후:
    py "C:/Dev/Sanjuk-Unreal/scripts/build_two_bone_leg_ik_rig.py"

동작:
  1. /Game/.../PC_01_CtrlRig_TwoBoneLegIK 에셋 존재 확인 (Monolith로 이미 복제됨)
  2. BeginExecution 제외 모든 노드 삭제 (FootClamp 복제로 생긴 잔여 노드)
  3. 좌/우 다리에 RigUnit_TwoBoneIKSimplePerItem 추가
  4. VB ik_foot_l/r GetTransform 연결 → Effector
  5. 핀 기본값 설정 (ItemA/B/Effector bone, Primary/Secondary Axis)
  6. 실행 체인 와이어: BeginExecution → TwoBoneIK_L → TwoBoneIK_R
  7. 컴파일 + 저장

롤백:
  실패 시: 에디터에서 PC_01_CtrlRig_TwoBoneLegIK 에셋 삭제.
  PC_01_CtrlRig_FootClamp 원본은 건드리지 않음.
"""

import unreal

ASSET_PATH = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_TwoBoneLegIK"
SOURCE_RIG = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_FootClamp"

# 좌/우 본이 mirrored된 커스텀 리그 — 사이드별 축 따로 설정
# 본 축 확인: 스켈레톤 열고 thigh_l / thigh_r 각각 선택 → 기즈모 X(빨강)/Y(초록)/Z(파랑) 방향 관찰
# 현재 R은 (X axis primary, secondary=0)으로 정상 → L은 X가 반대 방향일 가능성 높음

# 좌/우 축 (T포즈 정상 + 무릎 방향 제어를 위해 SecondaryAxis 활성)
# 오른쪽 (PrimaryAxis=X, SecondaryAxis=-Y 검증됨 — 사용자 확인)
PRIMARY_AXIS_R = "(X=1.000000,Y=0.000000,Z=0.000000)"
SECONDARY_AXIS_R = "(X=0.000000,Y=-1.000000,Z=0.000000)"

# 왼쪽 (mirrored — SecondaryAxis를 R 반대로 시도. L 휙휙 도는 증상 대응)
PRIMARY_AXIS_L = "(X=-1.000000,Y=0.000000,Z=0.000000)"
SECONDARY_AXIS_L = "(X=0.000000,Y=1.000000,Z=0.000000)"

# PoleVector: 현재 calf_l/r 위치를 그대로 사용 → 애니메이션 원본 무릎 방향 유지
# Direction/Location 상수 대신 GetTransform(calf) 노드 연결로 처리 (아래 add_unit + link 참조)
POLE_KIND = "Location"   # Translation 좌표를 사용

# SecondaryAxisWeight: 0=secondary 무시, 1=full pole 제어
# 경사/극단 포즈에서 무릎이 과도하게 벌어지면 이 값을 낮춤 (0.3~0.5 권장)
SECONDARY_WEIGHT = "0.500000"

DEBUG_DRAW = True


def log(msg):
    unreal.log(f"[TwoBoneLegIK] {msg}")


def err(msg):
    unreal.log_error(f"[TwoBoneLegIK] {msg}")


def main():
    eal = unreal.EditorAssetLibrary

    # 1) 에셋 존재 확인 — 없으면 복제
    if not eal.does_asset_exist(ASSET_PATH):
        log(f"Asset missing, duplicating from {SOURCE_RIG}")
        if not eal.duplicate_asset(SOURCE_RIG, ASSET_PATH):
            err("Duplicate failed.")
            return
    else:
        log(f"Asset exists: {ASSET_PATH}")

    rig_bp = eal.load_asset(ASSET_PATH)
    if rig_bp is None:
        err("Load failed.")
        return

    # 2) 컨트롤러 얻기
    try:
        controller = rig_bp.get_controller_by_name("RigVMModel")
    except Exception as e:
        err(f"get_controller_by_name failed: {e}")
        return
    if controller is None:
        err("Controller is None.")
        return

    # 3) BeginExecution 제외 모든 노드 삭제
    graph = controller.get_graph()
    nodes_to_remove = []
    begin_node_path = None
    for node in graph.get_nodes():
        np = node.get_node_path()
        # BeginExecution 인식: class 또는 path 에 BeginExecution 포함
        if "BeginExecution" in np or (hasattr(node, "get_script_struct") and node.get_script_struct() and "BeginExecution" in str(node.get_script_struct().get_path_name())):
            begin_node_path = np
            continue
        nodes_to_remove.append(np)

    log(f"Removing {len(nodes_to_remove)} existing nodes, keeping '{begin_node_path}'")
    for np in nodes_to_remove:
        try:
            controller.remove_node_by_name(np)
        except Exception as e:
            err(f"remove_node_by_name({np}) failed: {e}")

    # 4) TwoBoneIK 및 GetTransform 노드 추가
    TBIK_STRUCT = "/Script/ControlRig.RigUnit_TwoBoneIKSimplePerItem"
    GT_STRUCT = "/Script/ControlRig.RigUnit_GetTransform"

    def add_unit(struct_path, node_name, x, y):
        try:
            n = controller.add_unit_node_from_struct_path(
                struct_path, "Execute",
                unreal.Vector2D(x, y), node_name
            )
            if n is None:
                err(f"add_unit_node returned None for {node_name}")
            else:
                log(f"Added {node_name} at ({x},{y})")
            return n
        except Exception as e:
            err(f"add_unit({node_name}) failed: {e}")
            return None

    add_unit(TBIK_STRUCT, "TwoBoneIK_L", 1000, 200)
    add_unit(TBIK_STRUCT, "TwoBoneIK_R", 1500, 200)
    add_unit(GT_STRUCT, "GetIKFoot_L", 600, 500)
    add_unit(GT_STRUCT, "GetIKFoot_R", 1100, 500)
    # 무릎 현재 위치를 PoleVector로 — 애니메이션 원본 방향 유지
    add_unit(GT_STRUCT, "GetKnee_L", 400, 700)
    add_unit(GT_STRUCT, "GetKnee_R", 900, 700)

    # 5) 핀 기본값 세팅
    def set_pin(pin_path, value):
        try:
            ok = controller.set_pin_default_value(pin_path, value, False)
            if not ok:
                err(f"set_pin_default_value({pin_path} = {value}) returned False")
            return ok
        except Exception as e:
            err(f"set_pin({pin_path}={value}) failed: {e}")
            return False

    # 왼쪽
    set_pin("GetIKFoot_L.Item.Type", "Bone")
    set_pin("GetIKFoot_L.Item.Name", "VB ik_foot_l")
    set_pin("GetIKFoot_L.Space", "GlobalSpace")

    set_pin("TwoBoneIK_L.ItemA.Type", "Bone")
    set_pin("TwoBoneIK_L.ItemA.Name", "thigh_l")
    set_pin("TwoBoneIK_L.ItemB.Type", "Bone")
    set_pin("TwoBoneIK_L.ItemB.Name", "calf_l")
    set_pin("TwoBoneIK_L.EffectorItem.Type", "Bone")
    set_pin("TwoBoneIK_L.EffectorItem.Name", "foot_l")
    set_pin("TwoBoneIK_L.PrimaryAxis", PRIMARY_AXIS_L)
    set_pin("TwoBoneIK_L.SecondaryAxis", SECONDARY_AXIS_L)
    set_pin("TwoBoneIK_L.SecondaryAxisWeight", SECONDARY_WEIGHT)
    set_pin("TwoBoneIK_L.Weight", "1.000000")
    set_pin("TwoBoneIK_L.bEnableStretch", "False")
    set_pin("TwoBoneIK_L.bPropagateToChildren", "True")
    set_pin("TwoBoneIK_L.PoleVectorKind", POLE_KIND)
    # PoleVector는 GetKnee_L.Transform.Translation에서 link로 받음
    if DEBUG_DRAW:
        set_pin("TwoBoneIK_L.DebugSettings.bEnabled", "True")
        set_pin("TwoBoneIK_L.DebugSettings.Scale", "10.000000")

    # 오른쪽
    set_pin("GetIKFoot_R.Item.Type", "Bone")
    set_pin("GetIKFoot_R.Item.Name", "VB ik_foot_r")
    set_pin("GetIKFoot_R.Space", "GlobalSpace")

    set_pin("TwoBoneIK_R.ItemA.Type", "Bone")
    set_pin("TwoBoneIK_R.ItemA.Name", "thigh_r")
    set_pin("TwoBoneIK_R.ItemB.Type", "Bone")
    set_pin("TwoBoneIK_R.ItemB.Name", "calf_r")
    set_pin("TwoBoneIK_R.EffectorItem.Type", "Bone")
    set_pin("TwoBoneIK_R.EffectorItem.Name", "foot_r")
    set_pin("TwoBoneIK_R.PrimaryAxis", PRIMARY_AXIS_R)
    set_pin("TwoBoneIK_R.SecondaryAxis", SECONDARY_AXIS_R)
    set_pin("TwoBoneIK_R.SecondaryAxisWeight", SECONDARY_WEIGHT)
    set_pin("TwoBoneIK_R.Weight", "1.000000")
    set_pin("TwoBoneIK_R.bEnableStretch", "False")
    set_pin("TwoBoneIK_R.bPropagateToChildren", "True")
    set_pin("TwoBoneIK_R.PoleVectorKind", POLE_KIND)
    # PoleVector는 GetKnee_R.Transform.Translation에서 link로 받음
    if DEBUG_DRAW:
        set_pin("TwoBoneIK_R.DebugSettings.bEnabled", "True")
        set_pin("TwoBoneIK_R.DebugSettings.Scale", "10.000000")

    # GetKnee_L/R: calf 본 월드 위치 read
    set_pin("GetKnee_L.Item.Type", "Bone")
    set_pin("GetKnee_L.Item.Name", "calf_l")
    set_pin("GetKnee_L.Space", "GlobalSpace")
    set_pin("GetKnee_R.Item.Type", "Bone")
    set_pin("GetKnee_R.Item.Name", "calf_r")
    set_pin("GetKnee_R.Space", "GlobalSpace")

    # 6) 링크
    def link(src, tgt):
        try:
            ok = controller.add_link(src, tgt)
            if not ok:
                err(f"add_link({src} -> {tgt}) returned False")
            return ok
        except Exception as e:
            err(f"add_link({src} -> {tgt}) failed: {e}")
            return False

    # 실행 체인
    begin = begin_node_path or "RigUnit_BeginExecution"
    link(f"{begin}.ExecutePin", "TwoBoneIK_L.ExecutePin")
    link("TwoBoneIK_L.ExecutePin", "TwoBoneIK_R.ExecutePin")

    # Effector 연결
    link("GetIKFoot_L.Transform", "TwoBoneIK_L.Effector")
    link("GetIKFoot_R.Transform", "TwoBoneIK_R.Effector")

    # PoleVector ← calf 현재 위치 (애니메이션 원본 무릎 방향)
    link("GetKnee_L.Transform.Translation", "TwoBoneIK_L.PoleVector")
    link("GetKnee_R.Transform.Translation", "TwoBoneIK_R.PoleVector")

    # 7) 컴파일 + 저장
    try:
        log("Compiling...")
        unreal.BlueprintEditorLibrary.compile_blueprint(rig_bp)
    except Exception as e:
        err(f"Compile failed: {e}")

    try:
        eal.save_asset(ASSET_PATH)
        log("Saved.")
    except Exception as e:
        err(f"Save failed: {e}")

    log("Done. Open the rig in editor to verify visual graph.")
    log("Next step: in PC_01_AnimLayer_IK AnimGraph, insert new ControlRig node")
    log("(using this rig) between FootPlacement and existing FootClamp.")


main()
