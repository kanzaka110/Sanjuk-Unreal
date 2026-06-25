import unreal, traceback
OUT=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\spine_localyaw.txt"
DST="/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
GETXF="/Script/ControlRig.RigUnit_GetTransform"
TMAKE="/Script/RigVM.RigVMFunction_MathTransformMake"
TREL="/Script/RigVM.RigVMFunction_MathTransformMakeRelative"
DMUL="/Script/RigVM.RigVMFunction_MathDoubleMul"
DCLAMP="/Script/RigVM.RigVMFunction_MathDoubleClamp"
QAXIS="/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle"
OFF="/Script/ControlRig.RigUnit_OffsetTransformForItem"
K="0.008000"; CMAX="0.400000"; CMIN="-0.400000"
# (본, gain) 증분 yaw
BONES=[("spine_02","0.300000"),("spine_03","0.250000"),("neck_02","0.150000"),("head","0.100000")]
L=[]
def step(s):
    L.append(str(s))
    open(OUT,"w",encoding="utf-8").write("\n".join(L))
def main():
    bp=unreal.load_asset(DST); ctrl=bp.get_controller_by_name("RigVMModel"); g=ctrl.get_graph()
    # 1) AimBone 4 + orphan var 제거
    for nm in ("SpineAim_02","SpineAim_03","SpineAim_03_1","SpineAim_03_2"):
        try: ctrl.remove_node_by_name(nm); step(f"rm {nm}")
        except Exception as e: step(f"rm {nm} err {str(e)[:30]}")
    for n in list(g.get_nodes()):
        if n.get_class().get_name()=="RigVMVariableNode":
            outl=False
            for p in n.get_pins():
                if p.get_direction()==unreal.RigVMPinDirection.OUTPUT and len(p.get_linked_target_pins())>0: outl=True
            if not outl:
                try: ctrl.remove_node_by_name(n.get_node_path()); step(f"rm orphan {n.get_node_path()}")
                except Exception: pass
    def U(s,x,y,nm):
        n=ctrl.add_unit_node_from_struct_path(s,"Execute",unreal.Vector2D(x,y),nm)
        step(f"add {nm} -> {n.get_node_path() if n else None}"); return n
    def sp(p,v):
        ok=ctrl.set_pin_default_value(p,v,False)
        if not ok: step(f"PIN FALSE {p}={v}")
    def lk(a,b):
        try: ok=ctrl.add_link(a,b); step(f"{'lk' if ok else 'LKFALSE'} {a}->{b}")
        except Exception as e: step(f"LK ERR {a}->{b} {str(e)[:40]}")
    # 2) 공유 yaw 계산
    U(GETXF,-2000,-400,"SpineRef")
    sp("SpineRef.Item.Type","Bone"); sp("SpineRef.Item.Name","spine_03"); sp("SpineRef.Space","GlobalSpace")
    U(TMAKE,-2000,-250,"TgtXf")
    step("TgtXf pins="+str([p.get_name() for p in [n for n in g.get_nodes() if n.get_node_path()=="TgtXf"][0].get_pins()]))
    U(TREL,-1750,-350,"Rel")
    U(DMUL,-1500,-300,"MulK")
    U(DCLAMP,-1300,-300,"Yaw")
    lk("ToRig.Global","TgtXf.Translation")
    lk("TgtXf.Transform","Rel.Global")
    lk("SpineRef.Transform","Rel.Parent")
    lk("Rel.Local.Translation.Y","MulK.A")
    sp("MulK.B",K)
    lk("MulK.Result","Yaw.Value")
    sp("Yaw.Minimum",CMIN); sp("Yaw.Maximum",CMAX)
    # 3) 본별 offset
    prev_exec="RigUnit_BeginExecution.ExecutePin"
    x=-1000
    for bone,gain in BONES:
        mg=f"Mul_{bone}"; qa=f"Quat_{bone}"; of=f"Off_{bone}"
        U(DMUL,x,-200,mg); sp(f"{mg}.B",gain); lk("Yaw.Result",f"{mg}.A")
        U(QAXIS,x,-100,qa); sp(f"{qa}.Axis","(X=1.000000,Y=0.000000,Z=0.000000)"); lk(f"{mg}.Result",f"{qa}.Angle")
        U(OFF,x,0,of); sp(f"{of}.Item.Type","Bone"); sp(f"{of}.Item.Name",bone); sp(f"{of}.bPropagateToChildren","True")
        lk(f"{qa}.Result",f"{of}.OffsetTransform.Rotation")
        try: ctrl.bind_pin_to_variable(f"{of}.Weight","Weight"); step(f"bind {of}.Weight<-Weight")
        except Exception as e: step(f"bind err {str(e)[:30]}")
        lk(prev_exec,f"{of}.ExecutePin")
        prev_exec=f"{of}.ExecutePin"; x+=260
    # 4) 마지막 offset -> TwoBoneIK
    lk(prev_exec,"TwoBoneIK_R.ExecutePin")
    # exec 검증
    step("-- exec --")
    for l in g.get_links():
        s=l.get_source_pin().get_pin_path()
        if "ExecutePin" in s: step(f"  {s} -> {l.get_target_pin().get_pin_path()}")
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); step("compiled")
    unreal.EditorAssetLibrary.save_asset(DST); step("saved")
try: main()
except Exception: step("\n!!!"+traceback.format_exc())
