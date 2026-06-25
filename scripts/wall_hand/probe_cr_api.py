"""④ STAGE 0 probe v2: CR 변수/hierarchy API introspection + 팔 본 축. 무조건 파일 기록."""
import unreal
import traceback

OUT = r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\wallhand_cr_api.txt"
GUN = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_GunModeAim"

lines = []
def w(s): lines.append(str(s))


def safe(label, fn):
    try:
        w(f"  {label} = {fn()}")
    except Exception as e:
        w(f"  {label} ERR {str(e)[:90]}")


def main():
    bp = unreal.load_asset(GUN)
    ctrl = bp.get_controller_by_name("RigVMModel")

    w("=== dir(bp) [var/hier/member/local/external] ===")
    for a in dir(bp):
        al = a.lower()
        if any(k in al for k in ("variable", "hier", "member", "local", "external")):
            w("  bp." + a)

    w("\n=== dir(controller) [variable/external/local/add_node/add_variable] ===")
    for a in dir(ctrl):
        al = a.lower()
        if any(k in al for k in ("variable", "external", "local", "add_unit", "add_variable", "add_template")):
            w("  ctrl." + a)

    w("\n=== variable enumeration ===")
    safe("ctrl.get_graph().get_local_variables()", lambda: ctrl.get_graph().get_local_variables())
    if hasattr(bp, "get_local_variables"):
        safe("bp.get_local_variables()", lambda: bp.get_local_variables())
    if hasattr(bp, "get_member_variables"):
        safe("bp.get_member_variables()", lambda: bp.get_member_variables())
    # external variables on graph
    g = ctrl.get_graph()
    for m in ("get_external_variables", "get_variable_descriptions"):
        if hasattr(g, m):
            safe(f"graph.{m}()", lambda mm=m: getattr(g, mm)())

    w("\n=== VariableNode details ===")
    for n in g.get_nodes():
        if n.get_class().get_name() == "RigVMVariableNode":
            w(f"  node {n.get_node_path()}")
            for m in ("get_variable_name", "is_getter", "is_input_argument", "find_variable", "get_variable_description"):
                if hasattr(n, m):
                    safe(f"    .{m}()", lambda mm=m, nn=n: getattr(nn, mm)())

    w("\n=== hierarchy access ===")
    hier = None
    candidates = [
        ("bp.hierarchy", lambda: bp.hierarchy),
        ("bp.get_hierarchy_controller()", lambda: bp.get_hierarchy_controller()),
        ("bp.get_hierarchy_controller().get_hierarchy()", lambda: bp.get_hierarchy_controller().get_hierarchy()),
    ]
    for label, fn in candidates:
        try:
            val = fn()
            tn = type(val).__name__
            w(f"  {label} -> {tn}")
            if "RigHierarchy" in tn:
                hier = val
        except Exception as e:
            w(f"  {label} ERR {str(e)[:70]}")

    w("\n=== ARM AXES ===")
    if hier is None:
        w("  hierarchy not resolved")
    else:
        def gt(bone):
            key = unreal.RigElementKey(type=unreal.RigElementType.BONE, name=bone)
            try:
                return hier.get_global_transform(key, True)
            except Exception:
                return None
        for side in ("l", "r"):
            ua, la, ha = gt(f"upperarm_{side}"), gt(f"lowerarm_{side}"), gt(f"hand_{side}")
            if not (ua and la and ha):
                w(f"  side {side}: missing ua={ua is not None} la={la is not None} ha={ha is not None}")
                continue
            inv = ua.inverse()
            prim = inv.transform_vector(la.translation - ua.translation).normal()
            w(f"  {side}: UA={ua.translation} LA={la.translation} HA={ha.translation}")
            w(f"  {side}: PRIMARY(UA->LA, UA-local norm) = {prim}")


try:
    main()
except Exception:
    w("\n!!! TOP-LEVEL EXC:\n" + traceback.format_exc())

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
unreal.log(f"[wallhand_api] WROTE {OUT}")
