"""④ PC_01_CtrlRig_WallHandIK v3 (crash-safe, member-variable 조작 전무).
오른팔 위치 IK 메커니즘 검증용. target=기존 public var 'LookAtLocation' 재사용. Weight=상수 1.0.
add_unit / bind_pin_to_variable / add_link 크래시 여부를 증분 flush로 판정.
실행: py "<this>" / 결과 파일 회수.
"""
import unreal
import traceback

OUT = r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\wallhand_cr_build3.txt"
DST = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
SRC = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_GunModeAim"
TARGET_VAR = "LookAtLocation"  # 기존 public FVector 재사용 (= 월드 타겟)

TBIK = "/Script/ControlRig.RigUnit_TwoBoneIKSimplePerItem"
GETXF = "/Script/ControlRig.RigUnit_GetTransform"
TORIG = "/Script/ControlRig.RigUnit_ToRigSpace_Location"

lines = []
def step(s):
    lines.append(str(s))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    eal = unreal.EditorAssetLibrary
    step("START")
    if eal.does_asset_exist(DST):
        eal.delete_asset(DST); step("deleted existing")
    if not eal.duplicate_asset(SRC, DST):
        step("DUPLICATE FAILED"); return
    step("duplicated")
    bp = eal.load_asset(DST)
    ctrl = bp.get_controller_by_name("RigVMModel")
    graph = ctrl.get_graph()
    step("loaded")

    # strip (BeginExecution 외) — member variable은 그대로 둠
    begin = None; rm = []
    for n in graph.get_nodes():
        np = n.get_node_path(); ss = ""
        try:
            s = n.get_script_struct()
            if s: ss = s.get_name()
        except Exception:
            pass
        if "BeginExecution" in np or ss == "RigUnit_BeginExecution":
            begin = np
        else:
            rm.append(np)
    for np in rm:
        try:
            ctrl.remove_node_by_name(np)
        except Exception as e:
            step(f"strip ERR {np} {str(e)[:40]}")
    step(f"stripped, begin={begin}, nodes={[n.get_node_path() for n in graph.get_nodes()]}")

    # unit 노드 1개씩 (크래시 격리)
    def addunit(struct, x, y, nm):
        n = ctrl.add_unit_node_from_struct_path(struct, "Execute", unreal.Vector2D(x, y), nm)
        step(f"unit {nm} -> {n.get_node_path() if n else None}")
        return n
    addunit(TORIG, -500, 0, "ToRig")
    addunit(GETXF, -500, 300, "GetHand_R")
    addunit(GETXF, -500, 500, "GetElbow_R")
    addunit(TBIK, 0, 0, "TwoBoneIK_R")

    # 핀 디폴트
    def sp(path, val):
        try:
            ctrl.set_pin_default_value(path, val, False)
        except Exception as e:
            step(f"PIN ERR {path} {str(e)[:40]}")
    sp("GetHand_R.Item.Type","Bone"); sp("GetHand_R.Item.Name","hand_r"); sp("GetHand_R.Space","GlobalSpace")
    sp("GetElbow_R.Item.Type","Bone"); sp("GetElbow_R.Item.Name","lowerarm_r"); sp("GetElbow_R.Space","GlobalSpace")
    sp("TwoBoneIK_R.ItemA.Type","Bone"); sp("TwoBoneIK_R.ItemA.Name","upperarm_r")
    sp("TwoBoneIK_R.ItemB.Type","Bone"); sp("TwoBoneIK_R.ItemB.Name","lowerarm_r")
    sp("TwoBoneIK_R.EffectorItem.Type","Bone"); sp("TwoBoneIK_R.EffectorItem.Name","hand_r")
    sp("TwoBoneIK_R.PrimaryAxis","(X=-1.000000,Y=0.000000,Z=0.000000)")
    sp("TwoBoneIK_R.SecondaryAxisWeight","0.000000")
    sp("TwoBoneIK_R.PoleVectorKind","Location")
    sp("TwoBoneIK_R.bPropagateToChildren","True")
    sp("TwoBoneIK_R.Weight","1.000000")  # v1 상수(alpha 변수 없음)
    sp("TwoBoneIK_R.DebugSettings.bEnabled","True")
    sp("TwoBoneIK_R.DebugSettings.Scale","10.000000")
    step("pins set")

    # bind target pin <- 기존 변수 (getter 노드 미생성)
    try:
        r = ctrl.bind_pin_to_variable("ToRig.Value", TARGET_VAR)
        step(f"bind ToRig.Value <- {TARGET_VAR} ({r})")
    except Exception as e:
        step(f"bind ERR {str(e)[:70]}")

    # links
    def link(a, b):
        try:
            ok = ctrl.add_link(a, b); step(f"{'link' if ok else 'LINK-FALSE'} {a}->{b}")
        except Exception as e:
            step(f"LINK ERR {a}->{b} {str(e)[:50]}")
    link("ToRig.Global", "TwoBoneIK_R.Effector.Translation")
    link("GetHand_R.Transform.Rotation", "TwoBoneIK_R.Effector.Rotation")
    link("GetElbow_R.Transform.Translation", "TwoBoneIK_R.PoleVector")
    link(f"{begin}.ExecutePin", "TwoBoneIK_R.ExecutePin")

    try:
        unreal.BlueprintEditorLibrary.compile_blueprint(bp); step("compiled")
    except Exception as e:
        step(f"compile ERR {str(e)[:60]}")
    try:
        eal.save_asset(DST); step("saved")
    except Exception as e:
        step(f"save ERR {str(e)[:60]}")
    step("DONE")


try:
    main()
except Exception:
    lines.append("\n!!! EXC:\n" + traceback.format_exc())
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
unreal.log("[wallhand_cr3] end")
