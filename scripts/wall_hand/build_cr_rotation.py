"""④ 회전 추가: WallHandIK CR에 AimBone(손바닥→reach방향) 추가. TwoBoneIK 뒤.
reachDir = ToRig.Global(타겟) - upperarm_r 위치. 손바닥 로컬축 PALM_AXIS=(0,0,1) 추정(PIE flip).
Weight=alpha 게이트. 새 CR 변수 불필요(기존 입력만 사용).
"""
import unreal, traceback
OUT = r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\cr_rotation.txt"
DST = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
GETXF = "/Script/ControlRig.RigUnit_GetTransform"
AIM = "/Script/ControlRig.RigUnit_AimBone"
VSUB = "/Script/RigVM.RigVMFunction_MathVectorSub"
PALM_AXIS = "(X=0.000000,Y=1.000000,Z=0.000000)"  # 손바닥-바깥 = +Y (cross=손등 -Y의 반대). |Y|=0.99

lines = []
def step(s):
    lines.append(str(s))
    with open(OUT, "w", encoding="utf-8") as f: f.write("\n".join(lines))

def main():
    bp = unreal.load_asset(DST)
    ctrl = bp.get_controller_by_name("RigVMModel")
    g = ctrl.get_graph()
    existing = [n.get_node_path() for n in g.get_nodes()]
    step(f"existing={existing}")
    if "PalmAim" in existing:
        step("PalmAim 이미 존재 — 재빌드 위해 제거")
        for nm in ("PalmAim","GetUpper_R","ReachSub"):
            if nm in existing:
                try: ctrl.remove_node_by_name(nm)
                except Exception as e: step(f"rm {nm} err {str(e)[:40]}")

    def addunit(struct, x, y, nm):
        n = ctrl.add_unit_node_from_struct_path(struct, "Execute", unreal.Vector2D(x, y), nm)
        step(f"add {nm} -> {n.get_node_path() if n else None}")
        return n
    nUp = addunit(GETXF, 200, 500, "GetUpper_R")
    nSub = addunit(VSUB, 450, 400, "ReachSub")
    nAim = addunit(AIM, 700, 0, "PalmAim")

    # ReachSub 핀명 확인
    step("ReachSub pins=" + str([p.get_name() for p in nSub.get_pins()]))

    def sp(path, val):
        try:
            ok = ctrl.set_pin_default_value(path, val, False)
            if not ok: step(f"PIN FALSE {path}={val}")
        except Exception as e: step(f"PIN ERR {path} {str(e)[:50]}")
    sp("GetUpper_R.Item.Type","Bone"); sp("GetUpper_R.Item.Name","upperarm_r"); sp("GetUpper_R.Space","GlobalSpace")
    sp("PalmAim.Bone","hand_r")
    sp("PalmAim.Primary.Axis", PALM_AXIS)
    sp("PalmAim.Primary.Kind","Direction")
    sp("PalmAim.Primary.Weight","1.000000")
    sp("PalmAim.Secondary.Weight","0.000000")
    sp("PalmAim.bPropagateToChildren","True")
    sp("PalmAim.DebugSettings.bEnabled","True")
    sp("PalmAim.DebugSettings.Scale","15.000000")

    def link(a,b):
        try:
            ok = ctrl.add_link(a,b); step(f"{'link' if ok else 'LINK-FALSE'} {a}->{b}")
        except Exception as e: step(f"LINK ERR {a}->{b} {str(e)[:60]}")
    # reachDir = target(rig) - upperarm pos
    link("ToRig.Global", "ReachSub.A")
    link("GetUpper_R.Transform.Translation", "ReachSub.B")
    link("ReachSub.Result", "PalmAim.Primary.Target")
    # exec: TwoBoneIK_R -> PalmAim
    link("TwoBoneIK_R.ExecutePin", "PalmAim.ExecutePin")

    # Weight(overall) <- alpha 변수 (TwoBoneIK와 동일 게이트)
    try:
        r = ctrl.bind_pin_to_variable("PalmAim.Weight", "Weight")
        step(f"bind PalmAim.Weight<-Weight ({r})")
    except Exception as e: step(f"bind ERR {str(e)[:60]}")

    try:
        unreal.BlueprintEditorLibrary.compile_blueprint(bp); step("compiled")
    except Exception as e: step(f"compile ERR {str(e)[:60]}")
    try:
        unreal.EditorAssetLibrary.save_asset(DST); step("saved")
    except Exception as e: step(f"save ERR {str(e)[:60]}")
    step("DONE")

try: main()
except Exception: step("\n!!! EXC:\n"+traceback.format_exc())
unreal.log("[cr_rotation] end")
