import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/cr_latch_prep.json"
CR = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_CtrlRig_LedgeDangle"
result = {}
try:
    bp = unreal.load_asset(CR)
    result["variables"] = [str(v.name) for v in bp.get_member_variables()]
    c = bp.get_controller_by_name("RigVMModel") or bp.get_controller()
    g = c.get_graph()
    vnodes = []
    execchain = []
    for n in g.get_nodes():
        nm = str(n.get_node_path())
        if isinstance(n, unreal.RigVMVariableNode):
            vnodes.append({"node": nm, "var": str(n.get_variable_name()),
                           "getter": bool(n.is_getter())})
        # exec 체인: ExecuteContext 핀 링크
        for p in n.get_pins():
            pn = str(p.get_name())
            if "Execute" in pn:
                for l in p.get_links():
                    opp = str(l.get_opposite_pin(p).get_pin_path())
                    if p.get_direction() == unreal.RigVMPinDirection.OUTPUT:
                        execchain.append(nm + " -> " + opp)
    result["variable_nodes"] = vnodes
    result["exec_links"] = execchain
    # Sub_1/2 결과 소비자 (댕글 손 이펙터)
    subs = {}
    for n in g.get_nodes():
        nm = str(n.get_node_path())
        if "MathVectorSub" in nm and nm.endswith(("Sub_1", "Sub_2")):
            outs = []
            for p in n.get_pins():
                if str(p.get_name()) == "Result":
                    for l in p.get_links():
                        outs.append(str(l.get_opposite_pin(p).get_pin_path()))
            subs[nm] = outs
    result["sub_consumers"] = subs
except Exception:
    import traceback
    result["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(result, fp, indent=1)
print("CR_PREP_DONE")
