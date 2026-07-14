import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/ik_pole.json"
CR = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_CtrlRig_LedgeDangle"
result = {}
try:
    bp = unreal.load_asset(CR)
    c = bp.get_controller_by_name("RigVMModel") or bp.get_controller()
    g = c.get_graph()
    for n in g.get_nodes():
        nm = str(n.get_node_path())
        if "TwoBoneIK" not in nm:
            continue
        pins = {}
        for p in n.get_pins():
            pn = str(p.get_name())
            links = []
            for l in p.get_links():
                links.append(str(l.get_opposite_pin(p).get_pin_path()))
            try:
                dv = str(p.get_default_value())[:120]
            except Exception:
                dv = "?"
            pins[pn] = {"default": dv, "links": links}
        result[nm] = pins
except Exception:
    import traceback
    result["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(result, fp, indent=1)
print("IK_POLE_DONE")
