import unreal, traceback
OUT=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\yaw_units.txt"
DST="/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
UNITS=["/Script/ControlRig.RigUnit_OffsetTransformForItem",
       "/Script/RigVM.RigVMFunction_MathQuaternionFromAxisAndAngle",
       "/Script/ControlRig.RigUnit_GetRelativeTransformForItem",
       "/Script/RigVM.RigVMFunction_MathTransformMakeRelative",
       "/Script/RigVM.RigVMFunction_MathDoubleAtan",
       "/Script/RigVM.RigVMFunction_MathVectorMakeFromDouble"]
L=[]
def w(s): L.append(str(s))
try:
    bp=unreal.load_asset(DST); ctrl=bp.get_controller_by_name("RigVMModel")
    for i,u in enumerate(UNITS):
        try:
            n=ctrl.add_unit_node_from_struct_path(u,"Execute",unreal.Vector2D(3000,i*200),f"PROBE_{i}")
            if n:
                w(f"\n=== {u.split('.')[-1]} OK ===")
                for p in n.get_pins():
                    w(f"  {p.get_name()} ({p.get_direction()}) {p.get_cpp_type()}")
                ctrl.remove_node_by_name(n.get_node_path())
            else: w(f"\n{u} -> None")
        except Exception as e: w(f"\n{u.split('.')[-1]} ERR {str(e)[:60]}")
except Exception: w(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
