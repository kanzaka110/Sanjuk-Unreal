# -*- coding: utf-8 -*-
"""릴리즈 시 TwoBoneIK weight 페이드: fSelRelR/L(SelectBool) 삽입.
- Condition <- bWallHandLeft (미사용 var 재활용 = '릴리즈' 채널, 기본 false=현행 유지)
- IfTrue=0(릴리즈 -> weight 0, WInterp 감소속도 4로 스무스), IfFalse<-SelR/SelL.Result
- SelR/SelL.Result -> WInterpR/L.Value 링크를 fSelRel 경유로 교체.
"""
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260703_opt/cr_release_result.txt"
L = []
def w(s): L.append(str(s))
try:
    bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK")
    ctrl = bp.get_controller_by_name("RigVMModel")
    for side, sel, wint, x, y in (("R", "SelR", "WInterpR", -350, 620), ("L", "SelL", "WInterpL", -350, 900)):
        nm = "fSelRel%s" % side
        try:
            n = ctrl.add_unit_node_from_struct_path(
                "/Script/RigVM.RigVMFunction_MathFloatSelectBool", "Execute",
                unreal.Vector2D(x, y), nm)
            w("add %s OK" % nm)
        except Exception as e:
            w("add %s FAIL %s" % (nm, e)); continue
        try:
            ctrl.bind_pin_to_variable(nm + ".Condition", "bWallHandLeft", unreal.Vector2D(x - 220, y))
            w("bind %s.Condition <- bWallHandLeft OK" % nm)
        except Exception as e: w("bind FAIL %s" % e)
        try: ctrl.set_pin_default_value(nm + ".IfTrue", "0.000000", False); w("%s.IfTrue=0" % nm)
        except Exception as e: w("IfTrue FAIL %s" % e)
        try:
            ctrl.add_link(sel + ".Result", nm + ".IfFalse"); w("link %s.Result -> %s.IfFalse OK" % (sel, nm))
        except Exception as e: w("link IfFalse FAIL %s" % e)
        try:
            ctrl.break_link(sel + ".Result", wint + ".Value"); w("broke %s.Result -> %s.Value" % (sel, wint))
        except Exception as e: w("break FAIL %s" % e)
        try:
            ctrl.add_link(nm + ".Result", wint + ".Value"); w("link %s.Result -> %s.Value OK" % (nm, wint))
        except Exception as e: w("link WInterp FAIL %s" % e)
    ok = bp.recompile_vm() if hasattr(bp, "recompile_vm") else None
    w("recompile_vm called: %s" % ok)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp) if hasattr(unreal, "BlueprintEditorLibrary") else None
    w("DONE")
except Exception:
    w(traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(L))
