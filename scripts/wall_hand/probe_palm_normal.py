"""손바닥 법선 로컬축 정확 산출: hand_r 자식(너클) 위치로 손바닥 평면 normal 계산 → hand 로컬축 매핑."""
import unreal, traceback
OUT = r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\palm_normal.txt"
FOOT = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_FootClamp"
lines = []
def w(s): lines.append(str(s))

def main():
    bp = unreal.load_asset(FOOT)
    hier = bp.hierarchy
    ML = unreal.MathLibrary
    def key(b): return unreal.RigElementKey(type=unreal.RigElementType.BONE, name=b)
    def gt(b):
        try: return hier.get_global_transform(key(b), True)
        except Exception: return None
    # hand_r 자식 본 나열
    try:
        kids = hier.get_children(key("hand_r"))
        names = [k.name for k in kids]
    except Exception as e:
        names = f"err {e}"
    w(f"hand_r children = {names}")

    hand = gt("hand_r")
    # 너클 후보 (메타카르팔 끝/손가락 첫마디)
    idx = gt("index_metacarpal_r") or gt("index_01_r")
    mid = gt("middle_metacarpal_r") or gt("middle_01_r")
    pky = gt("pinky_metacarpal_r") or gt("pinky_01_r") or gt("ring_metacarpal_r") or gt("ring_01_r")
    w(f"hand={hand.translation if hand else None}")
    w(f"index={idx.translation if idx else None} middle={mid.translation if mid else None} pinky/ring={pky.translation if pky else None}")
    if not (hand and idx and pky and mid):
        w("필요 본 부족 — children 목록 보고 수동 지정 필요"); return
    # 손바닥 평면: across = pinky-index, along = middle-hand. normal = cross(along, across)
    across = ML.subtract_vector_vector(pky.translation, idx.translation)
    along = ML.subtract_vector_vector(mid.translation, hand.translation)
    n_world = ML.normal(ML.cross_vector_vector(along, across))
    n_world2 = ML.normal(ML.cross_vector_vector(across, along))  # 반대 부호
    n_local = ML.normal(ML.inverse_transform_direction(hand, n_world))
    n_local2 = ML.normal(ML.inverse_transform_direction(hand, n_world2))
    w(f"\npalm normal WORLD (cross along,across) = {n_world}")
    w(f"palm normal LOCAL = {n_local}")
    w(f"palm normal LOCAL (반대부호) = {n_local2}")
    w("=> LOCAL에서 |값| 최대인 축이 손바닥 법선축. 부호는 손바닥이 향하는 쪽.")

try: main()
except Exception: w("\n!!! EXC:\n"+traceback.format_exc())
with open(OUT,"w",encoding="utf-8") as f: f.write("\n".join(lines))
unreal.log("[palm_normal] done")
