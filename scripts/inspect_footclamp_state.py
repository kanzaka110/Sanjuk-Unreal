"""Inspect PC_01_CtrlRig_FootClamp current variable values + bone list.

Run inside Unreal Editor:
    exec(open("C:/Dev/Sanjuk-Unreal/scripts/inspect_footclamp_state.py").read())
"""
from __future__ import annotations

import unreal

CR_PATH: str = "/Game/ART/Character/PC/PC_01/Rig/PC_01_CtrlRig_FootClamp"


def section(t: str) -> None:
    print("\n" + "=" * 70)
    print(t)
    print("=" * 70)


def main() -> None:
    bp = unreal.load_asset(CR_PATH)
    if not bp:
        print("load fail")
        return

    section("RigVM variables (default values)")
    try:
        vars_ = bp.get_editor_property("new_variables")
        if vars_:
            for v in vars_:
                try:
                    name = v.var_name
                    type_name = getattr(v, "var_type", None)
                    default = getattr(v, "default_value", None)
                    print(f"  {name}  type={type_name}  default={default}")
                except Exception:
                    print(f"  {v}")
    except Exception as e:
        print("err:", e)

    # Alternative: controller's graph local variables
    section("controller local variables / graph inspection")
    try:
        model = bp.get_default_model()
        ctrl = bp.get_or_create_controller(model)
        graph = ctrl.get_graph()

        # Variables on nodes (VariableNode defaults)
        for n in graph.get_nodes():
            try:
                cls = n.get_class().get_name()
                if "Variable" not in cls:
                    continue
                name = n.get_name()
                # find the Variable pin
                var_pin = None
                val_pin = None
                for p in n.get_pins():
                    pname = p.get_name()
                    if pname == "Variable":
                        var_pin = p
                    elif pname == "Value":
                        val_pin = p
                var_name = (
                    ctrl.get_pin_default_value(var_pin.get_pin_path())
                    if var_pin else "?"
                )
                val_default = (
                    ctrl.get_pin_default_value(val_pin.get_pin_path())
                    if val_pin else "?"
                )
                print(f"  {name}  -> Variable={var_name}  "
                      f"CurrentValueDefault={val_default}")
            except Exception as e:
                print(f"  node err: {e}")
    except Exception as e:
        print("err:", e)

    section("BoneNames default (the array iterated by For_Each)")
    try:
        for n in graph.get_nodes():
            try:
                if n.get_name() != "VariableNode":
                    continue
                # VariableNode at start — reads 'BoneNames'
                for p in n.get_pins():
                    pname = p.get_name()
                    if pname == "Variable":
                        print(f"  Variable: "
                              f"{ctrl.get_pin_default_value(p.get_pin_path())}")
                    elif pname == "Value":
                        print(f"  Value pin path: {p.get_pin_path()}")
                        print(f"  Value default:  "
                              f"{ctrl.get_pin_default_value(p.get_pin_path())}")
            except Exception as e:
                print(f"  node err: {e}")
    except Exception as e:
        print("err:", e)

    # CDO default values for BP-level variables (actual runtime defaults)
    section("Blueprint CDO default values")
    try:
        gen = bp.get_editor_property("generated_class")
        if gen:
            cdo = unreal.get_default_object(gen)
            for var_name in ["BoneNames", "Angle_Clamp_Pitch",
                             "Angle_Clamp_Roll", "Angle_Clamp_Yaw"]:
                try:
                    val = cdo.get_editor_property(var_name)
                    print(f"  {var_name} = {val}")
                except Exception as e:
                    print(f"  {var_name} ?? {type(e).__name__}: "
                          f"{str(e)[:60]}")
    except Exception as e:
        print("err:", e)

    section("Rig hierarchy entries + event list")
    try:
        hierarchy = bp.get_editor_property("hierarchy")
        print(f"  hierarchy: {hierarchy}")
    except Exception:
        pass
    try:
        # list events / entry nodes
        for n in graph.get_nodes():
            cls = n.get_class().get_name()
            if "BeginExecution" in n.get_name() or "Entry" in cls:
                print(f"  entry: {n.get_name()}  class={cls}")
    except Exception:
        pass

    section("Check for Backwards Solve event")
    try:
        has_inverse = False
        for n in graph.get_nodes():
            try:
                title = n.get_node_title()
            except Exception:
                title = ""
            if "Backwards" in str(title) or "Inverse" in str(title):
                print(f"  found: {n.get_name()}  title={title}")
                has_inverse = True
        if not has_inverse:
            print("  no Backwards/Inverse Solve event (forward-only)")
    except Exception as e:
        print("err:", e)


main()
