"""Aim 유닛 핀 구조 확인 (WallHandIK CR에 임시 추가→덤프). 회전 빌드용."""
import unreal, traceback
OUT = r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\aim_pins.txt"
DST = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
lines = []
def w(s): lines.append(str(s))

def dump(node, pre="  "):
    for p in node.get_pins():
        try:
            w(f"{pre}{p.get_name()} : {p.get_cpp_type()} = {p.get_default_value()!r}")
            for sp in p.get_sub_pins():
                w(f"{pre}    .{sp.get_name()} : {sp.get_cpp_type()} = {sp.get_default_value()!r}")
        except Exception as e:
            w(f"{pre}<pin err {str(e)[:50]}>")

try:
    bp = unreal.load_asset(DST)
    ctrl = bp.get_controller_by_name("RigVMModel")
    for struct in ("/Script/ControlRig.RigUnit_AimBone",
                   "/Script/ControlRig.RigUnit_AimItem",
                   "/Script/ControlRig.RigUnit_AimBoneSimple"):
        try:
            n = ctrl.add_unit_node_from_struct_path(struct, "Execute", unreal.Vector2D(2000, 600), "PROBE_AIM")
            if n:
                w(f"=== {struct} OK -> {n.get_node_path()} ===")
                dump(n)
                ctrl.remove_node_by_name(n.get_node_path())
                w("(removed)")
                break
            else:
                w(f"{struct} -> None")
        except Exception as e:
            w(f"{struct} ERR {str(e)[:70]}")
except Exception:
    w("\n!!! EXC:\n"+traceback.format_exc())
with open(OUT,"w",encoding="utf-8") as f: f.write("\n".join(lines))
unreal.log("[aim probe] done")
