"""④ v1 CR: 기존 'Weight' 변수(double) public화 + TwoBoneIK_R.Weight 에 bind = alpha 게이트.
기본값 0 -> IK off (AnimLayer 안전 삽입). add_member_variable 회피(재사용).
"""
import unreal, traceback
OUT = r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\wallhand_alpha.txt"
DST = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
lines = []
def step(s):
    lines.append(str(s))
    with open(OUT, "w", encoding="utf-8") as f: f.write("\n".join(lines))
try:
    bp = unreal.load_asset(DST)
    ctrl = bp.get_controller_by_name("RigVMModel")
    step("loaded")
    # Weight 변수 public(instance editable)
    try:
        bp.set_blueprint_variable_instance_editable("Weight", True)
        step("Weight set instance_editable=True")
    except Exception as e:
        step(f"set_editable ERR {str(e)[:80]}")
    # bind TwoBoneIK_R.Weight <- Weight (1.0 상수 대체)
    try:
        r = ctrl.bind_pin_to_variable("TwoBoneIK_R.Weight", "Weight")
        step(f"bind TwoBoneIK_R.Weight <- Weight ({r})")
    except Exception as e:
        step(f"bind ERR {str(e)[:80]}")
    try:
        unreal.BlueprintEditorLibrary.compile_blueprint(bp); step("compiled")
    except Exception as e:
        step(f"compile ERR {str(e)[:60]}")
    try:
        unreal.EditorAssetLibrary.save_asset(DST); step("saved")
    except Exception as e:
        step(f"save ERR {str(e)[:60]}")
    # 검증: public 변수 + Weight 핀 바인딩
    step("\n-- member vars --")
    for v in bp.get_member_variables():
        step(f"  {v.get_editor_property('name')} : {v.get_editor_property('cpp_type')} public={v.get_editor_property('public')}")
    step("-- links --")
    for lk in ctrl.get_graph().get_links():
        step(f"  {lk.get_source_pin().get_pin_path()} -> {lk.get_target_pin().get_pin_path()}")
    step("DONE")
except Exception:
    step("\n!!! EXC:\n" + traceback.format_exc())
unreal.log("[wallhand_alpha] done")
