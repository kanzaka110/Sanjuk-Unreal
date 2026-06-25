"""④ STAGE 0 probe v3: 팔 축(수정) + ToRigSpace_Location / TwoBoneIKSimplePerItem 핀 경로."""
import unreal
import traceback

OUT = r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\wallhand_pins.txt"
GUN = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_GunModeAim"
FOOT = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_FootClamp"

lines = []
def w(s): lines.append(str(s))


def dump_pins(node, prefix="  "):
    try:
        pins = node.get_pins()
    except Exception as e:
        w(prefix + f"<get_pins err {str(e)[:60]}>"); return
    for p in pins:
        try:
            nm = p.get_name()
            ct = p.get_cpp_type()
            dv = p.get_default_value()
            w(f"{prefix}{nm} : {ct} = {dv!r}")
            sub = p.get_sub_pins()
            for sp in sub:
                w(f"{prefix}    .{sp.get_name()} : {sp.get_cpp_type()} = {sp.get_default_value()!r}")
        except Exception as e:
            w(prefix + f"<pin err {str(e)[:60]}>")


def find_node(bp, name):
    ctrl = bp.get_controller_by_name("RigVMModel")
    for n in ctrl.get_graph().get_nodes():
        if n.get_node_path() == name:
            return n
    return None


def main():
    # 1) 팔 축 (MathLibrary.inverse_transform_direction 사용)
    w("=== ARM AXES (FootClamp hierarchy) ===")
    bpf = unreal.load_asset(FOOT)
    hier = bpf.hierarchy
    ML = unreal.MathLibrary
    def gt(b):
        k = unreal.RigElementKey(type=unreal.RigElementType.BONE, name=b)
        try: return hier.get_global_transform(k, True)
        except Exception: return None
    for side in ("l", "r"):
        ua, la, ha = gt(f"upperarm_{side}"), gt(f"lowerarm_{side}"), gt(f"hand_{side}")
        if not (ua and la and ha):
            w(f"  {side}: missing"); continue
        # primary = (UA->LA) dir into UA local
        dir_ua = ML.subtract_vector_vector(la.translation, ua.translation)
        prim = ML.inverse_transform_direction(ua, dir_ua)
        prim = ML.normal(prim)
        # secondary candidate = bend plane normal into UA local: cross(seg1,seg2)
        seg1 = ML.normal(ML.subtract_vector_vector(la.translation, ua.translation))
        seg2 = ML.normal(ML.subtract_vector_vector(ha.translation, la.translation))
        bend_w = ML.cross_vector_vector(seg1, seg2)
        bend_ua = ML.normal(ML.inverse_transform_direction(ua, bend_w))
        w(f"  {side}: PRIMARY(UA->LA, UA-local) = {prim}")
        w(f"  {side}: BENDPLANE_NORMAL(UA-local) = {bend_ua}")

    # 2) ToRigSpace_Location 핀 (GunModeAim 'From World_1_1')
    w("\n=== ToRigSpace_Location pins (GunModeAim) ===")
    bpg = unreal.load_asset(GUN)
    n = find_node(bpg, "From World_1_1")
    if n: dump_pins(n)
    else: w("  node not found")

    # 3) TwoBoneIKSimplePerItem 핀 (FootClamp)
    w("\n=== TwoBoneIKSimplePerItem pins (FootClamp) ===")
    n = find_node(bpf, "RigUnit_TwoBoneIKSimplePerItem")
    if n: dump_pins(n)
    else: w("  node not found")


try:
    main()
except Exception:
    w("\n!!! EXC:\n" + traceback.format_exc())

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
unreal.log(f"[wallhand_pins] WROTE {OUT}")
