"""오른팔 팔꿈치의 자연스러운 pole 방향을 spine_03 로컬 공간으로 산출(데이터 기반).
pole_dir = (elbow - midpoint(shoulder,hand)) 를 spine_03 로컬로. 몸-상대 = 몸 돌아도 유효.
"""
import unreal, traceback
OUT = r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\elbow_pole.txt"
FOOT = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_FootClamp"
lines=[]
def w(s): lines.append(str(s))
try:
    bp=unreal.load_asset(FOOT); hier=bp.hierarchy; ML=unreal.MathLibrary
    def gt(b):
        k=unreal.RigElementKey(type=unreal.RigElementType.BONE,name=b)
        return hier.get_global_transform(k,True)
    ua=gt("upperarm_r"); la=gt("lowerarm_r"); ha=gt("hand_r"); sp=gt("spine_03")
    mid=ML.multiply_vector_float(ML.add_vector_vector(ua.translation,ha.translation),0.5)
    pole_world=ML.normal(ML.subtract_vector_vector(la.translation,mid))
    pole_local=ML.normal(ML.inverse_transform_direction(sp,pole_world))
    w(f"upperarm_r={ua.translation}")
    w(f"lowerarm_r(elbow)={la.translation}")
    w(f"hand_r={ha.translation}")
    w(f"midpoint(sh,hand)={mid}")
    w(f"pole dir WORLD = {pole_world}")
    w(f"pole dir spine_03-LOCAL = {pole_local}")
    w("=> 이 LOCAL 방향을 PoleVector(Direction)+PoleVectorSpace=spine_03 에 넣으면 몸-상대 팔꿈치 방향 유지")
except Exception:
    w("ERR "+traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(lines))
unreal.log("[elbow_pole] done")
