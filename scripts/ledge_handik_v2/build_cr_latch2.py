import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/cr_latch_build2.json"
CR = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_CtrlRig_LedgeDangle"
log = {"steps": []}


def step(msg):
    log["steps"].append(str(msg))


try:
    bp = unreal.load_asset(CR)
    c = bp.get_controller_by_name("RigVMModel") or bp.get_controller()
    g = c.get_graph()

    def link(a, b):
        try:
            ok = c.add_link(a, b)
            step(("LINK OK " if ok else "LINK FAIL ") + a + " -> " + b)
        except Exception as e:
            step("LINK ERR " + a + " -> " + b + " : " + repr(e)[:100])

    def brk(a, b):
        try:
            c.break_link(a, b)
            step("BREAK " + a + " -> " + b)
        except Exception as e:
            step("BREAK ERR " + a + " -> " + b + " : " + repr(e)[:100])

    def setdef(pin, val):
        try:
            c.set_pin_default_value(pin, val, False)
            step("DEF " + pin + " = " + val)
        except Exception as e:
            step("DEF ERR " + pin + " : " + repr(e)[:100])

    # --- L ---
    link("RigVMFunction_MathVectorSub_1.Result", "LatchToWorldL.Location")
    link("VariableNode_4.Value", "LatchLessL.A")
    setdef("LatchLessL.B", "0.5")
    link("LatchLessL.Result", "LatchSelL.Condition")
    link("LatchToWorldL.Result", "LatchSelL.IfTrue")
    link("VariableNode_1.Value", "LatchSelL.IfFalse")
    link("LatchSelL.Result", "VariableNode_6.Value")
    link("LatchInvM2W.Result", "LatchToCompL.Transform")
    link("VariableNode_1.Value", "LatchToCompL.Location")
    brk("VariableNode_1.Value", "RigVMFunction_MathVectorLerp.B")
    link("LatchToCompL.Result", "RigVMFunction_MathVectorLerp.B")
    # --- R ---
    link("VariableNode_5.Value", "LatchToWorldR.Transform")
    link("RigVMFunction_MathVectorSub_2.Result", "LatchToWorldR.Location")
    link("VariableNode_3.Value", "LatchLessR.A")
    setdef("LatchLessR.B", "0.5")
    link("LatchLessR.Result", "LatchSelR.Condition")
    link("LatchToWorldR.Result", "LatchSelR.IfTrue")
    link("VariableNode_2.Value", "LatchSelR.IfFalse")
    link("LatchSelR.Result", "VariableNode_7.Value")
    link("LatchInvM2W.Result", "LatchToCompR.Transform")
    link("VariableNode_2.Value", "LatchToCompR.Location")
    brk("VariableNode_2.Value", "RigVMFunction_MathVectorLerp_1.B")
    link("LatchToCompR.Result", "RigVMFunction_MathVectorLerp_1.B")

    # --- exec 체인 끝 → Set 2개 ---
    exec_out = {}
    exec_pin_name = {}
    for n in g.get_nodes():
        nm = str(n.get_node_path())
        for p in n.get_pins():
            try:
                cpp = str(p.get_cpp_type())
            except Exception:
                cpp = ""
            if cpp == "FRigVMExecuteContext":
                exec_pin_name[nm] = str(p.get_name())
                outs = []
                for l in p.get_links():
                    src = str(l.get_source_pin().get_pin_path())
                    tgt = str(l.get_target_pin().get_pin_path())
                    if src.startswith(nm + "."):
                        outs.append(tgt)
                exec_out[nm] = exec_out.get(nm, []) + outs
    log["exec_map"] = exec_out
    tail = None
    for nm, outs in exec_out.items():
        if nm in ("VariableNode_6", "VariableNode_7") or "BeginExecution" in nm:
            continue
        if len(outs) == 0:
            tail = nm
    step("exec tail = " + str(tail))
    if tail:
        link(tail + "." + exec_pin_name[tail], "VariableNode_6.ExecuteContext")
        link("VariableNode_6.ExecuteContext", "VariableNode_7.ExecuteContext")

    bp.recompile_vm()
    step("recompiled")
    saved = unreal.EditorAssetLibrary.save_asset(CR, only_if_is_dirty=False)
    log["saved"] = bool(saved)
except Exception:
    import traceback
    log["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(log, fp, indent=1)
print("CR_LATCH2_DONE")
