import unreal, traceback
OUT=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\spine_unify.txt"
DST="/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
# (노드, 본, secondary weight)  아래->위 점감
NODES=[("SpineAim_02","spine_02","0.200000"),
       ("SpineAim_03","spine_03","0.150000"),
       ("SpineAim_03_2","neck_02","0.100000"),
       ("SpineAim_03_1","head","0.050000")]
# 통일 secondary 템플릿 (기존 head 노드 기준)
SAXIS="(X=0.000000,Y=1.000000,Z=0.000000)"   # 측면 Y축
STARGET="(X=1.000000,Y=0.000000,Z=0.000000)" # 전방 X
L=[]
def w(s): L.append(str(s))
try:
    bp=unreal.load_asset(DST); ctrl=bp.get_controller_by_name("RigVMModel")
    def sp(p,v):
        ok=ctrl.set_pin_default_value(p,v,False); w(("OK " if ok else "FALSE ")+p+"="+v)
    for nm,bone,sw in NODES:
        sp(f"{nm}.Bone",bone)
        sp(f"{nm}.Primary.Weight","0.000000")            # primary off 유지
        sp(f"{nm}.Secondary.Axis",SAXIS)
        sp(f"{nm}.Secondary.Kind","Direction")
        sp(f"{nm}.Secondary.Target",STARGET)
        sp(f"{nm}.Secondary.Weight",sw)
        sp(f"{nm}.DebugSettings.Scale","5.000000")
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); w("compiled")
    unreal.EditorAssetLibrary.save_asset(DST); w("saved")
except Exception: w(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
