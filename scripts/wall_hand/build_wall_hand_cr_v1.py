"""④ PC_01_CtrlRig_WallHandIK v1 빌드 (오른팔 위치 IK only).
베이스=FootClamp 복제(하이어라키 확보)→BeginExecution 외 스트립→멤버변수 정리→
멤버변수 4종 추가→getter/ToRigSpace/GetTransform/TwoBoneIK 배선→compile+save.
원본 FootClamp 불변. 실패 시 신규 에셋 삭제로 롤백.
실행: py "<this>"  / 결과 파일 회수.
"""
import unreal
import traceback

OUT = r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\wallhand_cr_build.txt"
DST = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
SRC = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_FootClamp"

TBIK = "/Script/ControlRig.RigUnit_TwoBoneIKSimplePerItem"
GETXF = "/Script/ControlRig.RigUnit_GetTransform"
TORIG = "/Script/ControlRig.RigUnit_ToRigSpace_Location"

lines = []
def w(s): lines.append(str(s))
def flush():
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    unreal.log(f"[wallhand_cr] WROTE {OUT}")


def main():
    eal = unreal.EditorAssetLibrary
    # 1) 복제
    if eal.does_asset_exist(DST):
        w(f"DST exists, deleting for clean rebuild: {DST}")
        eal.delete_asset(DST)
    if not eal.duplicate_asset(SRC, DST):
        w("DUPLICATE FAILED"); return
    w(f"duplicated {SRC} -> {DST}")
    bp = eal.load_asset(DST)
    ctrl = bp.get_controller_by_name("RigVMModel")
    graph = ctrl.get_graph()

    # 2) BeginExecution 외 전 노드 스트립
    begin = None
    rm = []
    for n in graph.get_nodes():
        np = n.get_node_path()
        ss = ""
        try:
            s = n.get_script_struct()
            if s: ss = s.get_name()
        except Exception:
            pass
        if "BeginExecution" in np or ss == "RigUnit_BeginExecution":
            begin = np
        else:
            rm.append(np)
    w(f"begin={begin}  strip {len(rm)} nodes")
    for np in rm:
        try:
            ctrl.remove_node_by_name(np)
        except Exception as e:
            w(f"  rm {np} ERR {str(e)[:50]}")
    w(f"remaining nodes: {[n.get_node_path() for n in graph.get_nodes()]}")

    # 3) 멤버변수 정리
    try:
        mv = [v.get_editor_property('name') if hasattr(v,'get_editor_property') else v['name'] for v in bp.get_member_variables()]
    except Exception:
        mv = []
    w(f"existing member vars: {mv}")
    try:
        bp.bulk_remove_member_variables([unreal.Name(str(m)) for m in mv])
        w("bulk_remove_member_variables ok")
    except Exception as e:
        w(f"bulk_remove ERR {str(e)[:80]}")

    # 4) 멤버변수 4종 (public=노출 핀)
    def addvar(name, cpp):
        try:
            r = bp.add_member_variable(name, cpp, True, False, "")
            w(f"  addvar {name}:{cpp} -> {r}")
        except Exception as e:
            w(f"  addvar {name} ERR {str(e)[:80]}")
    addvar("WallHandTarget", "FVector")
    addvar("WallHandNormal", "FVector")
    addvar("WallHandAlpha", "float")
    addvar("bWallHandRight", "bool")

    # 5) 노드 추가
    VEC = unreal.Vector.static_struct()
    def addvarnode(name, cpp, obj, x, y, nodename):
        try:
            n = ctrl.add_variable_node(name, cpp, obj, True, "", unreal.Vector2D(x, y), nodename)
            w(f"  varnode {nodename}({name}) -> {n.get_node_path() if n else None}")
            return n
        except Exception as e:
            w(f"  varnode {nodename} ERR {str(e)[:90]}")
            return None
    def addunit(struct, x, y, nodename):
        try:
            n = ctrl.add_unit_node_from_struct_path(struct, "Execute", unreal.Vector2D(x, y), nodename)
            w(f"  unit {nodename} -> {n.get_node_path() if n else None}")
            return n
        except Exception as e:
            w(f"  unit {nodename} ERR {str(e)[:90]}")
            return None

    nGetTarget = addvarnode("WallHandTarget", "FVector", VEC, -800, 0, "GetTarget")
    nGetAlpha  = addvarnode("WallHandAlpha", "float", None, -800, 200, "GetAlpha")
    nToRig     = addunit(TORIG, -500, 0, "ToRig")
    nHandR     = addunit(GETXF, -500, 300, "GetHand_R")
    nElbowR    = addunit(GETXF, -500, 500, "GetElbow_R")
    nIKR       = addunit(TBIK, 0, 0, "TwoBoneIK_R")

    # 6) 핀 디폴트
    def sp(path, val):
        try:
            ok = ctrl.set_pin_default_value(path, val, False)
            if not ok: w(f"  PIN FALSE {path}={val}")
        except Exception as e:
            w(f"  PIN ERR {path}={val} {str(e)[:60]}")
    sp("GetHand_R.Item.Type", "Bone");  sp("GetHand_R.Item.Name", "hand_r");      sp("GetHand_R.Space", "GlobalSpace")
    sp("GetElbow_R.Item.Type", "Bone"); sp("GetElbow_R.Item.Name", "lowerarm_r"); sp("GetElbow_R.Space", "GlobalSpace")
    sp("TwoBoneIK_R.ItemA.Type", "Bone");        sp("TwoBoneIK_R.ItemA.Name", "upperarm_r")
    sp("TwoBoneIK_R.ItemB.Type", "Bone");        sp("TwoBoneIK_R.ItemB.Name", "lowerarm_r")
    sp("TwoBoneIK_R.EffectorItem.Type", "Bone"); sp("TwoBoneIK_R.EffectorItem.Name", "hand_r")
    sp("TwoBoneIK_R.PrimaryAxis", "(X=-1.000000,Y=0.000000,Z=0.000000)")  # R = -X (data-driven)
    sp("TwoBoneIK_R.SecondaryAxisWeight", "0.000000")
    sp("TwoBoneIK_R.PoleVectorKind", "Location")
    sp("TwoBoneIK_R.bPropagateToChildren", "True")
    sp("TwoBoneIK_R.DebugSettings.bEnabled", "True")
    sp("TwoBoneIK_R.DebugSettings.Scale", "10.000000")

    # 7) 링크
    def link(a, b):
        try:
            ok = ctrl.add_link(a, b)
            w(f"  {'LINK' if ok else 'LINK-FALSE'} {a} -> {b}")
        except Exception as e:
            w(f"  LINK ERR {a}->{b} {str(e)[:70]}")
    link(f"{nGetTarget.get_node_path()}.Value", "ToRig.Value")
    link("ToRig.Global", "TwoBoneIK_R.Effector.Translation")
    link("GetHand_R.Transform.Rotation", "TwoBoneIK_R.Effector.Rotation")
    link("GetElbow_R.Transform.Translation", "TwoBoneIK_R.PoleVector")
    link(f"{nGetAlpha.get_node_path()}.Value", "TwoBoneIK_R.Weight")
    link(f"{begin}.ExecutePin", "TwoBoneIK_R.ExecutePin")

    # 8) compile + save
    try:
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        w("compiled")
    except Exception as e:
        w(f"compile ERR {str(e)[:80]}")
    try:
        eal.save_asset(DST)
        w("saved")
    except Exception as e:
        w(f"save ERR {str(e)[:80]}")
    w("DONE")


try:
    main()
except Exception:
    w("\n!!! EXC:\n" + traceback.format_exc())
flush()
