"""스파인 본 forward/up 로컬축 산출 (체스트를 벽으로 Aim 하기 위해).
ref 포즈에서 각 spine 본의 월드 기저축 → 캐릭터 forward(월드+X)/up(월드+Z)에 가까운 로컬축 식별.
"""
import unreal, traceback
OUT = r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\spine_axes.txt"
FOOT = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_FootClamp"
lines = []
def w(s): lines.append(str(s))
def main():
    bp = unreal.load_asset(FOOT)
    hier = bp.hierarchy
    ML = unreal.MathLibrary
    def gt(b):
        k = unreal.RigElementKey(type=unreal.RigElementType.BONE, name=b)
        try: return hier.get_global_transform(k, True)
        except Exception: return None
    FWD = unreal.Vector(1,0,0); UP = unreal.Vector(0,0,1)
    def axis_world(rot, lx,ly,lz):
        return rot.rotate_vector(unreal.Vector(lx,ly,lz))
    for b in ("spine_01","spine_02","spine_03","spine_04","spine_05"):
        t = gt(b)
        if t is None:
            w(f"{b}: missing"); continue
        r = t.rotation
        xs = axis_world(r,1,0,0); ys = axis_world(r,0,1,0); zs = axis_world(r,0,0,1)
        # 각 로컬축의 월드 forward/up 정렬도(dot)
        def d(v, ref): return round(ML.dot_vector_vector(v, ref),3)
        w(f"\n{b}:")
        w(f"  X world={xs}  dotFWD={d(xs,FWD)} dotUP={d(xs,UP)}")
        w(f"  Y world={ys}  dotFWD={d(ys,FWD)} dotUP={d(ys,UP)}")
        w(f"  Z world={zs}  dotFWD={d(zs,FWD)} dotUP={d(zs,UP)}")
    w("\n=> dotFWD ~ +1 인 로컬축 = 체스트 forward(전방). dotUP ~ +1 = 스파인 up.")
try: main()
except Exception: w("\n!!! EXC:\n"+traceback.format_exc())
with open(OUT,"w",encoding="utf-8") as f: f.write("\n".join(lines))
unreal.log("[spine_axes] done")
