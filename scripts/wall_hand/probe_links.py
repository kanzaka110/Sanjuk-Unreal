"""④ STAGE 0 probe v4: GunModeAim 링크 전수 + ToRigSpace 핀 방향. 월드->rig 패턴 확정."""
import unreal
import traceback

OUT = r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\wallhand_links.txt"
GUN = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_GunModeAim"

lines = []
def w(s): lines.append(str(s))


def main():
    bp = unreal.load_asset(GUN)
    ctrl = bp.get_controller_by_name("RigVMModel")
    g = ctrl.get_graph()

    w("=== GunModeAim LINKS ===")
    try:
        for lk in g.get_links():
            src = lk.get_source_pin(); tgt = lk.get_target_pin()
            w(f"  {src.get_pin_path()}  ->  {tgt.get_pin_path()}")
    except Exception as e:
        w(f"  links err {str(e)[:90]}")

    w("\n=== ToRigSpace 'From World_1_1' pin directions ===")
    for n in g.get_nodes():
        if n.get_node_path() == "From World_1_1":
            for p in n.get_pins():
                try:
                    w(f"  {p.get_name()} dir={p.get_direction()} type={p.get_cpp_type()}")
                except Exception as e:
                    w(f"  pin err {str(e)[:60]}")

    w("\n=== add_member_variable signature hint ===")
    try:
        import inspect
        w("  " + str(inspect.signature(bp.add_member_variable)))
    except Exception as e:
        w(f"  sig err {str(e)[:80]}")
    # help string fallback
    try:
        w("  doc: " + (bp.add_member_variable.__doc__ or "")[:300])
    except Exception as e:
        w(f"  doc err {str(e)[:60]}")


try:
    main()
except Exception:
    w("\n!!! EXC:\n" + traceback.format_exc())

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
unreal.log(f"[wallhand_links] WROTE {OUT}")
