"""스파인 보정: spine_02/03 을 벽 타겟으로 살짝 Aim(전방 -Z), alpha 게이트, TwoBoneIK 앞에 삽입.
벽에 붙을수록(alpha↑) 상체가 벽 쪽으로 돌아 팔 과회전 경감.
재실행 시 기존 SpineAim 제거 후 재빌드(orphan 방지). 새 CR 입력 불필요.
"""
import unreal, traceback
OUT = r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\spine_assist.txt"
DST = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
AIM = "/Script/ControlRig.RigUnit_AimBone"
FWD = "(X=0.000000,Y=0.000000,Z=-1.000000)"   # 체스트 전방 = -Z 로컬
UP  = "(X=1.000000,Y=0.000000,Z=0.000000)"    # 스파인 up = +X 로컬
lines = []
def step(s):
    lines.append(str(s))
    with open(OUT,"w",encoding="utf-8") as f: f.write("\n".join(lines))

def main():
    bp = unreal.load_asset(DST)
    ctrl = bp.get_controller_by_name("RigVMModel")
    g = ctrl.get_graph()
    have = [n.get_node_path() for n in g.get_nodes()]
    step(f"before={have}")
    for nm in ("SpineAim_02","SpineAim_03"):
        if nm in have:
            try: ctrl.remove_node_by_name(nm); step(f"removed old {nm}")
            except Exception as e: step(f"rm {nm} err {str(e)[:40]}")

    def addaim(x,y,nm):
        n = ctrl.add_unit_node_from_struct_path(AIM,"Execute",unreal.Vector2D(x,y),nm)
        step(f"add {nm} -> {n.get_node_path() if n else None}")
        return n
    s2 = addaim(-1000, -400, "SpineAim_02")
    s3 = addaim(-700, -400, "SpineAim_03")

    def sp(path,val):
        ok = ctrl.set_pin_default_value(path,val,False)
        if not ok: step(f"FALSE {path}={val}")
    for nm, bone, pw in (("SpineAim_02","spine_02","0.300000"), ("SpineAim_03","spine_03","0.400000")):
        sp(f"{nm}.Bone", bone)
        sp(f"{nm}.Primary.Axis", FWD)
        sp(f"{nm}.Primary.Kind", "Location")   # 타겟 '지점'을 향함
        sp(f"{nm}.Primary.Weight", pw)
        sp(f"{nm}.Secondary.Axis", UP)
        sp(f"{nm}.Secondary.Kind", "Direction")
        sp(f"{nm}.Secondary.Target", "(X=0.000000,Y=0.000000,Z=1.000000)")
        sp(f"{nm}.Secondary.Weight", "1.000000")
        sp(f"{nm}.bPropagateToChildren", "True")
        sp(f"{nm}.DebugSettings.bEnabled", "True")
        sp(f"{nm}.DebugSettings.Scale", "20.000000")

    def link(a,b):
        try:
            ok = ctrl.add_link(a,b); step(f"{'link' if ok else 'LINK-FALSE'} {a}->{b}")
        except Exception as e: step(f"LINK ERR {a}->{b} {str(e)[:50]}")
    def brk(a,b):
        for m in ("break_link","break_all_links"):
            if hasattr(ctrl,m):
                try:
                    if m=="break_link": ctrl.break_link(a,b)
                    step(f"broke {a}->{b}"); return
                except Exception as e: step(f"brk err {str(e)[:40]}")
    # 타겟(벽지점, rig) -> 각 spine Primary.Target
    link("ToRig.Global", "SpineAim_02.Primary.Target")
    link("ToRig.Global", "SpineAim_03.Primary.Target")
    # overall Weight <- alpha
    for nm in ("SpineAim_02","SpineAim_03"):
        try:
            r = ctrl.bind_pin_to_variable(f"{nm}.Weight", "Weight"); step(f"bind {nm}.Weight<-Weight ({r})")
        except Exception as e: step(f"bind ERR {nm} {str(e)[:50]}")
    # exec 재배치: Begin -> Spine02 -> Spine03 -> TwoBoneIK_R
    brk("RigUnit_BeginExecution.ExecutePin", "TwoBoneIK_R.ExecutePin")
    link("RigUnit_BeginExecution.ExecutePin", "SpineAim_02.ExecutePin")
    link("SpineAim_02.ExecutePin", "SpineAim_03.ExecutePin")
    link("SpineAim_03.ExecutePin", "TwoBoneIK_R.ExecutePin")

    # exec 검증
    step("\n-- exec links --")
    for lk in g.get_links():
        s = lk.get_source_pin().get_pin_path(); t = lk.get_target_pin().get_pin_path()
        if "ExecutePin" in s:
            step(f"  {s} -> {t}")

    try: unreal.BlueprintEditorLibrary.compile_blueprint(bp); step("compiled")
    except Exception as e: step(f"compile ERR {str(e)[:50]}")
    try: unreal.EditorAssetLibrary.save_asset(DST); step("saved")
    except Exception as e: step(f"save ERR {str(e)[:50]}")
    step("DONE")

try: main()
except Exception: step("\n!!! EXC:\n"+traceback.format_exc())
unreal.log("[spine_assist] end")
