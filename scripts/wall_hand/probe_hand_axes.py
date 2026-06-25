"""v2 준비: hand_r/hand_l 본의 월드 기저축(X/Y/Z) + 손가락 본 방향 = 손바닥 법선축 추정."""
import unreal, traceback
OUT = r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\hand_axes.txt"
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
    # 후보 손가락/하위 본 (있으면 손바닥/손방향 추정)
    finger_candidates = ["middle_metacarpal_r","index_metacarpal_r","middle_01_r","index_01_r","hand_r"]
    for side in ("r","l"):
        ha = gt(f"hand_{side}")
        la = gt(f"lowerarm_{side}")
        if ha is None:
            w(f"hand_{side} missing"); continue
        rot = ha.rotation
        # 손 본 로컬축의 월드 방향
        xw = ML.quat_rotate_vector(rot, unreal.Vector(1,0,0)) if hasattr(ML,"quat_rotate_vector") else rot.rotate_vector(unreal.Vector(1,0,0))
        yw = rot.rotate_vector(unreal.Vector(0,1,0))
        zw = rot.rotate_vector(unreal.Vector(0,0,1))
        w(f"\n=== hand_{side} (월드 기저축) ===")
        w(f"  pos={ha.translation}")
        w(f"  X-axis world = {xw}")
        w(f"  Y-axis world = {yw}")
        w(f"  Z-axis world = {zw}")
        if la is not None:
            armdir = ML.normal(ML.subtract_vector_vector(ha.translation, la.translation))
            w(f"  arm dir(lowerarm->hand) world = {armdir}  (이 방향에 가까운 축 = 손 길이방향)")
        # 손가락 본으로 손 forward 추정
        for fb in finger_candidates:
            ft = gt(f"{fb if fb.endswith('_'+side) else fb}")
            if ft is not None and fb != f"hand_{side}":
                fdir = ML.normal(ML.subtract_vector_vector(ft.translation, ha.translation))
                w(f"  -> {fb}: dir(hand->finger) world = {fdir}")
                break

try:
    main()
except Exception:
    w("\n!!! EXC:\n"+traceback.format_exc())
with open(OUT,"w",encoding="utf-8") as f: f.write("\n".join(lines))
unreal.log("[hand_axes] done")
