"""④ PC_01_CtrlRig_WallHandIK v2 (crash-safe). 오른팔 위치 IK only.
변경: 베이스=GunModeAim(소형 strip) / getter노드 대신 bind_pin_to_variable / 매 단계 flush.
실행: py "<this>"  / 결과 파일 회수(소켓 끊겨도 파일이 진실).
"""
import unreal
import traceback

OUT = r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\wallhand_cr_build2.txt"
DST = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
SRC = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_GunModeAim"

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
        eal.delete_asset(DST); step(f"deleted existing {DST}")
    if not eal.duplicate_asset(SRC, DST):
        step("DUPLICATE FAILED"); return
    step(f"duplicated {SRC} -> {DST}")
    bp = eal.load_asset(DST)
    ctrl = bp.get_controller_by_name("RigVMModel")
    graph = ctrl.get_graph()
    step("loaded bp+controller")

    # 본 존재 확인 (read-only, 무크래시)
    hier = bp.hierarchy
    missing = []
    for b in ("upperarm_r", "lowerarm_r", "hand_r"):
        k = unreal.RigElementKey(type=unreal.RigElementType.BONE, name=b)
        try:
            t = hier.get_global_transform(k, True)
            if t is None: missing.append(b)
        except Exception:
            missing.append(b)
    step(f"bone check missing={missing}")
    if missing:
        step("ABORT: arm bones missing in this base rig"); return

    # strip (BeginExecution 외)
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
    step(f"begin={begin} strip_targets={rm}")
    for np in rm:
        try:
            ctrl.remove_node_by_name(np); step(f"stripped {np}")
        except Exception as e:
            step(f"strip ERR {np} {str(e)[:50]}")
    step(f"after strip nodes={[n.get_node_path() for n in graph.get_nodes()]}")

    # member vars 정리 + 추가
    try:
        mv = [str(v.get_editor_property('name')) for v in bp.get_member_variables()]
    except Exception as e:
        mv = []; step(f"get_member_variables ERR {str(e)[:60]}")
    step(f"existing vars={mv}")
    if mv:
        try:
            bp.bulk_remove_member_variables([unreal.Name(m) for m in mv]); step("bulk_removed vars")
        except Exception as e:
            step(f"bulk_remove ERR {str(e)[:60]}")
    for name, cpp in (("WallHandTarget","FVector"),("WallHandNormal","FVector"),
                      ("WallHandAlpha","float"),("bWallHandRight","bool")):
        try:
            bp.add_member_variable(name, cpp, True, False, ""); step(f"addvar {name}:{cpp}")
        except Exception as e:
            step(f"addvar {name} ERR {str(e)[:70]}")

    # unit 노드 1개씩 (크래시 격리)
    def addunit(struct, x, y, nm):
        n = ctrl.add_unit_node_from_struct_path(struct, "Execute", unreal.Vector2D(x, y), nm)
        step(f"unit {nm} -> {n.get_node_path() if n else None}")
        return n
    nToRig = addunit(TORIG, -500, 0, "ToRig")
    nHandR = addunit(GETXF, -500, 300, "GetHand_R")
    nElbowR = addunit(GETXF, -500, 500, "GetElbow_R")
    nIKR = addunit(TBIK, 0, 0, "TwoBoneIK_R")

    # 핀 디폴트
    def sp(path, val):
        try:
            ctrl.set_pin_default_value(path, val, False)
        except Exception as e:
            step(f"PIN ERR {path} {str(e)[:50]}")
    sp("GetHand_R.Item.Type","Bone"); sp("GetHand_R.Item.Name","hand_r"); sp("GetHand_R.Space","GlobalSpace")
    sp("GetElbow_R.Item.Type","Bone"); sp("GetElbow_R.Item.Name","lowerarm_r"); sp("GetElbow_R.Space","GlobalSpace")
    sp("TwoBoneIK_R.ItemA.Type","Bone"); sp("TwoBoneIK_R.ItemA.Name","upperarm_r")
    sp("TwoBoneIK_R.ItemB.Type","Bone"); sp("TwoBoneIK_R.ItemB.Name","lowerarm_r")
    sp("TwoBoneIK_R.EffectorItem.Type","Bone"); sp("TwoBoneIK_R.EffectorItem.Name","hand_r")
    sp("TwoBoneIK_R.PrimaryAxis","(X=-1.000000,Y=0.000000,Z=0.000000)")
    sp("TwoBoneIK_R.SecondaryAxisWeight","0.000000")
    sp("TwoBoneIK_R.PoleVectorKind","Location")
    sp("TwoBoneIK_R.bPropagateToChildren","True")
    sp("TwoBoneIK_R.DebugSettings.bEnabled","True")
    sp("TwoBoneIK_R.DebugSettings.Scale","10.000000")
    step("pins set")

    # bind_pin_to_variable (getter 노드 회피)
    def bind(pin, var):
        try:
            r = ctrl.bind_pin_to_variable(pin, var)
            step(f"bind {pin} <- {var}  ({r})")
        except Exception as e:
            step(f"bind ERR {pin}<-{var} {str(e)[:70]}")
    bind("ToRig.Value", "WallHandTarget")
    bind("TwoBoneIK_R.Weight", "WallHandAlpha")

    # links
    def link(a, b):
        try:
            ok = ctrl.add_link(a, b); step(f"{'link' if ok else 'LINK-FALSE'} {a}->{b}")
        except Exception as e:
            step(f"LINK ERR {a}->{b} {str(e)[:60]}")
    link("ToRig.Global", "TwoBoneIK_R.Effector.Translation")
    link("GetHand_R.Transform.Rotation", "TwoBoneIK_R.Effector.Rotation")
    link("GetElbow_R.Transform.Translation", "TwoBoneIK_R.PoleVector")
    link(f"{begin}.ExecutePin", "TwoBoneIK_R.ExecutePin")

    try:
        unreal.BlueprintEditorLibrary.compile_blueprint(bp); step("compiled")
    except Exception as e:
        step(f"compile ERR {str(e)[:70]}")
    try:
        eal.save_asset(DST); step("saved")
    except Exception as e:
        step(f"save ERR {str(e)[:70]}")
    step("DONE")


try:
    main()
except Exception:
    lines.append("\n!!! EXC:\n" + traceback.format_exc())
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
unreal.log("[wallhand_cr2] end")
