"""B안: 팔꿈치(PoleVector) 안정화 + 스파인 보정 재투입.
1) TwoBoneIK PoleVector = 월드-다운 방향 고정(elbow flip 방지). 기존 GetElbow 링크 끊음.
2) SpineAim_02/03 재추가(전방 -Z 를 벽 타겟에 Aim, gentle weight, alpha 게이트), Begin 직후 삽입.
exec: Begin -> Spine02 -> Spine03 -> TwoBoneIK -> PalmAim.
"""
import unreal, traceback
OUT = r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\spine_v2.txt"
DST = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
AIM = "/Script/ControlRig.RigUnit_AimBone"
FWD = "(X=0.000000,Y=0.000000,Z=-1.000000)"   # 체스트 전방 = -Z
UP  = "(X=1.000000,Y=0.000000,Z=0.000000)"    # 스파인 up = +X
W2="0.200000"; W3="0.250000"                   # 스파인 보정 강도(튜닝 노브)
lines=[]
def step(s):
    lines.append(str(s))
    with open(OUT,"w",encoding="utf-8") as f: f.write("\n".join(lines))
def main():
    bp=unreal.load_asset(DST); ctrl=bp.get_controller_by_name("RigVMModel"); g=ctrl.get_graph()
    have=[n.get_node_path() for n in g.get_nodes()]; step(f"before={have}")

    # ---- 1) PoleVector 안정화: 월드-다운 방향 고정 ----
    try: ctrl.break_link("GetElbow_R.Transform.Translation","TwoBoneIK_R.PoleVector"); step("broke GetElbow->PoleVector")
    except Exception as e: step(f"break pole err {str(e)[:40]}")
    def sp(p,v):
        ok=ctrl.set_pin_default_value(p,v,False); step(f"{'OK' if ok else 'FALSE'} {p}={v}")
    sp("TwoBoneIK_R.PoleVectorKind","Direction")
    sp("TwoBoneIK_R.PoleVector","(X=0.000000,Y=0.000000,Z=-1.000000)")

    # ---- 2) 스파인 재추가 ----
    for nm in ("SpineAim_02","SpineAim_03"):
        if nm in have:
            try: ctrl.remove_node_by_name(nm)
            except Exception: pass
    def addaim(x,y,nm):
        n=ctrl.add_unit_node_from_struct_path(AIM,"Execute",unreal.Vector2D(x,y),nm); step(f"add {nm}->{n.get_node_path() if n else None}"); return n
    addaim(-1000,-400,"SpineAim_02"); addaim(-700,-400,"SpineAim_03")
    for nm,bone,pw in (("SpineAim_02","spine_02",W2),("SpineAim_03","spine_03",W3)):
        sp(f"{nm}.Bone",bone)
        sp(f"{nm}.Primary.Axis",FWD); sp(f"{nm}.Primary.Kind","Location"); sp(f"{nm}.Primary.Weight",pw)
        sp(f"{nm}.Secondary.Axis",UP); sp(f"{nm}.Secondary.Kind","Direction"); sp(f"{nm}.Secondary.Target","(X=0.000000,Y=0.000000,Z=1.000000)"); sp(f"{nm}.Secondary.Weight","1.000000")
        sp(f"{nm}.bPropagateToChildren","True"); sp(f"{nm}.DebugSettings.bEnabled","True"); sp(f"{nm}.DebugSettings.Scale","5.000000")
    def link(a,b):
        try: ok=ctrl.add_link(a,b); step(f"{'link' if ok else 'LINK-FALSE'} {a}->{b}")
        except Exception as e: step(f"LINK ERR {a}->{b} {str(e)[:40]}")
    link("ToRig.Global","SpineAim_02.Primary.Target"); link("ToRig.Global","SpineAim_03.Primary.Target")
    for nm in ("SpineAim_02","SpineAim_03"):
        try: ctrl.bind_pin_to_variable(f"{nm}.Weight","Weight"); step(f"bind {nm}.Weight<-Weight")
        except Exception as e: step(f"bind err {str(e)[:40]}")

    # ---- exec 재배치: Begin -> Spine02 -> Spine03 -> TwoBoneIK ----
    try: ctrl.break_link("RigUnit_BeginExecution.ExecutePin","TwoBoneIK_R.ExecutePin"); step("broke Begin->TwoBoneIK")
    except Exception as e: step(f"break exec err {str(e)[:40]}")
    link("RigUnit_BeginExecution.ExecutePin","SpineAim_02.ExecutePin")
    link("SpineAim_02.ExecutePin","SpineAim_03.ExecutePin")
    link("SpineAim_03.ExecutePin","TwoBoneIK_R.ExecutePin")

    step("-- exec links --")
    for lk in g.get_links():
        s=lk.get_source_pin().get_pin_path()
        if "ExecutePin" in s: step(f"  {s} -> {lk.get_target_pin().get_pin_path()}")
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); step("compiled")
    unreal.EditorAssetLibrary.save_asset(DST); step("saved"); step("DONE")
try: main()
except Exception: step("\n!!!"+traceback.format_exc())
unreal.log("[spine_v2] end")
