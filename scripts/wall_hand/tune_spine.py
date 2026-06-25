"""SpineAim weight 완화(살짝) + 디버그 축소. 핀만 수정."""
import unreal, traceback
OUT = r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\tune_spine.txt"
DST = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
# 튜닝 노브 (여기만 바꾸면 됨)
W2 = "0.000000"   # spine_02 primary weight  (진단: 스파인 OFF)
W3 = "0.000000"   # spine_03 primary weight  (진단: 스파인 OFF)
lines = []
def w(s): lines.append(str(s))
try:
    bp = unreal.load_asset(DST)
    ctrl = bp.get_controller_by_name("RigVMModel")
    def sp(p,v):
        ok = ctrl.set_pin_default_value(p,v,False); w(f"{'OK' if ok else 'FALSE'} {p}={v}")
    sp("SpineAim_02.Primary.Weight", W2)
    sp("SpineAim_03.Primary.Weight", W3)
    sp("SpineAim_02.DebugSettings.Scale","5.000000")
    sp("SpineAim_03.DebugSettings.Scale","5.000000")
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); w("compiled")
    unreal.EditorAssetLibrary.save_asset(DST); w("saved")
except Exception:
    w("\n!!! EXC:\n"+traceback.format_exc())
with open(OUT,"w",encoding="utf-8") as f: f.write("\n".join(lines))
unreal.log("[tune_spine] done")
