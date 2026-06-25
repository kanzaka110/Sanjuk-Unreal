"""PalmAim 핀만 수정(노드 추가/제거 없음=orphan 무):
Primary.Axis +Y(손바닥-바깥), Secondary(손가락 -X → 위) 롤 고정.
"""
import unreal, traceback
OUT = r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\tune_palm.txt"
DST = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
lines = []
def w(s): lines.append(str(s))
try:
    bp = unreal.load_asset(DST)
    ctrl = bp.get_controller_by_name("RigVMModel")
    def sp(path, val):
        ok = ctrl.set_pin_default_value(path, val, False)
        w(f"{'OK' if ok else 'FALSE'} {path}={val}")
    # Primary: 손바닥-바깥 = +Y, reach방향으로
    sp("PalmAim.Primary.Axis", "(X=0.000000,Y=1.000000,Z=0.000000)")
    sp("PalmAim.Primary.Kind", "Direction")
    sp("PalmAim.Primary.Weight", "1.000000")
    # Secondary: 손가락(-X) → 월드 위(0,0,1) 로 롤 고정
    sp("PalmAim.Secondary.Axis", "(X=-1.000000,Y=0.000000,Z=0.000000)")
    sp("PalmAim.Secondary.Kind", "Direction")
    sp("PalmAim.Secondary.Target", "(X=0.000000,Y=0.000000,Z=1.000000)")
    sp("PalmAim.Secondary.Weight", "1.000000")
    # 확인
    for n in ctrl.get_graph().get_nodes():
        if n.get_node_path() == "PalmAim":
            for p in n.get_pins():
                if p.get_name() in ("Primary","Secondary"):
                    w(f"PalmAim.{p.get_name()} = {p.get_default_value()!r}")
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); w("compiled")
    unreal.EditorAssetLibrary.save_asset(DST); w("saved")
except Exception:
    w("\n!!! EXC:\n"+traceback.format_exc())
with open(OUT,"w",encoding="utf-8") as f: f.write("\n".join(lines))
unreal.log("[tune_palm] done")
