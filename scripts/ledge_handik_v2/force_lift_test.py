# 강제 리프트 테스트 — SlopeLiftWeight.B 를 인자로 세팅 (기본 -20, 원복은 1.0)
# py force_lift_test.py [-20.0 | 1.0]
import unreal, sys

CR = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_CtrlRig_LedgeDangle"
val = sys.argv[1] if len(sys.argv) > 1 else "-20.0"
bp = unreal.load_asset(CR)
c = bp.get_controller_by_name("RigVMModel") or bp.get_controller()
c.set_pin_default_value("SlopeLiftWeight.B", val, False)
bp.recompile_vm()
saved = unreal.EditorAssetLibrary.save_asset(CR, only_if_is_dirty=False)
print("SlopeLiftWeight.B =", val, "| recompiled | saved =", bool(saved))
