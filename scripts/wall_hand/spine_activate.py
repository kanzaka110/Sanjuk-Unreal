import unreal, traceback
OUT=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\spine_activate.txt"
DST="/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
# (노드, 본, primary weight) 아래->위 점감, 작게(미세 turn)
NODES=[("SpineAim_02","spine_02","0.150000"),
       ("SpineAim_03","spine_03","0.100000"),
       ("SpineAim_03_2","neck_02","0.060000"),
       ("SpineAim_03_1","head","0.030000")]
FWD="(X=0.000000,Y=0.000000,Z=-1.000000)"   # 체스트 전방 -Z
UP ="(X=1.000000,Y=0.000000,Z=0.000000)"    # 스파인 up +X
L=[]
def w(s): L.append(str(s))
try:
    bp=unreal.load_asset(DST); ctrl=bp.get_controller_by_name("RigVMModel")
    def sp(p,v):
        ok=ctrl.set_pin_default_value(p,v,False); w(("OK " if ok else "FALSE ")+p+"="+v)
    for nm,bone,pw in NODES:
        sp(f"{nm}.Bone",bone)
        # Primary 켜기: 전방 -Z 를 벽 타겟(지점)에
        sp(f"{nm}.Primary.Axis",FWD)
        sp(f"{nm}.Primary.Kind","Location")
        sp(f"{nm}.Primary.Weight",pw)
        # Primary.Target <- ToRig.Global (이미 연결됐으면 무시)
        try: 
            ok=ctrl.add_link("ToRig.Global",f"{nm}.Primary.Target"); w(f"link ToRig->{nm}.Primary.Target ({ok})")
        except Exception as e: w(f"link {nm} skip ({str(e)[:30]})")
        # Secondary: 상체 수직 유지
        sp(f"{nm}.Secondary.Axis",UP)
        sp(f"{nm}.Secondary.Kind","Direction")
        sp(f"{nm}.Secondary.Target","(X=0.000000,Y=0.000000,Z=1.000000)")
        sp(f"{nm}.Secondary.Weight","1.000000")
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); w("compiled")
    unreal.EditorAssetLibrary.save_asset(DST); w("saved")
except Exception: w(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
