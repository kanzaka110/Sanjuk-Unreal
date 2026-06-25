import unreal, traceback
OUT=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\add_reachdamp.txt"
DST="/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
L=[]
def w(s): L.append(str(s))
try:
    bp=unreal.load_asset(DST); ctrl=bp.get_controller_by_name("RigVMModel")
    path="/Script/RigVM.RigVMFunction_DampVector"
    node=ctrl.add_unit_node_from_struct_path(path,"Execute",unreal.Vector2D(-600,-600),"ReachDamp")
    w(f"add ReachDamp -> {node.get_node_path() if node else None}")
    if node:
        for p in node.get_pins():
            w(f"  pin {p.get_name()} dir={p.get_direction()} type={p.get_cpp_data_type()}")
    # set smoothing time default
    ok=ctrl.set_pin_default_value("ReachDamp.SmoothingTime","0.080000")
    w(f"set SmoothingTime=0.08 ({ok})")
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); w("compiled")
    unreal.EditorAssetLibrary.save_asset(DST); w("saved")
except Exception: w(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
