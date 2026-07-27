# CR 손 리치 클램프 조정 — py set_reach_clamp.py [값]  (기본 52, 원복 44.5)
import unreal, sys

CR = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_CtrlRig_LedgeDangle"
val = sys.argv[1] if len(sys.argv) > 1 else "52.0"
bp = unreal.load_asset(CR)
c = bp.get_controller_by_name("RigVMModel") or bp.get_controller()
for side in ("L", "R"):
    c.set_pin_default_value("ReachClamp%s.MaximumLength" % side, val, False)
bp.recompile_vm()
saved = unreal.EditorAssetLibrary.save_asset(CR, only_if_is_dirty=False)
print("ReachClampL/R.MaximumLength =", val, "| recompiled | saved =", bool(saved))
