"""팔꿈치 관통 해결: pole을 spine_03 로컬 '아래+바깥(+Y)' 방향으로 고정.
GetElbow(Location) 끊고 -> PoleVectorKind=Direction, PoleVectorSpace=spine_03, PoleVector=(down+out).
spine_03 로컬: +X=위, +Y=캐릭터 오른쪽(바깥), +Z=뒤. 팔꿈치=아래(-X)+바깥(+Y).
POLE 노브: 여기 바꿔서 튜닝.
"""
import unreal, traceback
OUT = r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\outward_pole.txt"
DST = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
POLE = "(X=-0.600000,Y=0.800000,Z=0.000000)"   # 아래(-X) + 바깥(+Y). 관통하면 Y↑, 닭날개면 X↓(더 아래)
lines=[]
def w(s): lines.append(str(s))
try:
    bp=unreal.load_asset(DST); ctrl=bp.get_controller_by_name("RigVMModel")
    # GetElbow Location 링크 끊기
    try: ctrl.break_link("GetElbow_R.Transform.Translation","TwoBoneIK_R.PoleVector"); w("broke GetElbow->PoleVector")
    except Exception as e: w(f"break: {str(e)[:40]} (이미 끊겼을 수 있음)")
    def sp(p,v):
        ok=ctrl.set_pin_default_value(p,v,False); w(f"{'OK' if ok else 'FALSE'} {p}={v}")
    sp("TwoBoneIK_R.PoleVectorKind","Direction")
    sp("TwoBoneIK_R.PoleVectorSpace.Type","Bone")
    sp("TwoBoneIK_R.PoleVectorSpace.Name","spine_03")
    sp("TwoBoneIK_R.PoleVector",POLE)
    # 확인
    for n in ctrl.get_graph().get_nodes():
        if n.get_node_path()=="TwoBoneIK_R":
            for pn in n.get_pins():
                if pn.get_name() in ("PoleVector","PoleVectorKind","PoleVectorSpace"):
                    w(f"  {pn.get_name()} = {pn.get_default_value()!r}")
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); w("compiled")
    unreal.EditorAssetLibrary.save_asset(DST); w("saved")
except Exception:
    w("ERR "+traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(lines))
unreal.log("[outward_pole] done")
