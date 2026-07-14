import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/cr_latch_build.json"
CR = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_CtrlRig_LedgeDangle"
log = {"steps": []}


def step(msg):
    log["steps"].append(str(msg))


try:
    bp = unreal.load_asset(CR)
    c = bp.get_controller_by_name("RigVMModel") or bp.get_controller()
    g = c.get_graph()

    def add_unit(path, name, pos):
        n = c.add_unit_node_from_struct_path(path, "Execute", unreal.Vector2D(pos[0], pos[1]), name)
        if n is None:
            raise RuntimeError("add_unit failed: " + path)
        step("created %s (%s)" % (name, path))
        return str(n.get_node_path())

    # 1) 노드 생성
    inv = add_unit("/Script/RigVM.RigVMFunction_MathTransformInverse", "LatchInvM2W", (100, 1200))
    twL = add_unit("/Script/RigVM.RigVMFunction_MathTransformTransformVector", "LatchToWorldL", (300, 1100))
    twR = add_unit("/Script/RigVM.RigVMFunction_MathTransformTransformVector", "LatchToWorldR", (300, 1400))
    lsL = add_unit("/Script/RigVM.RigVMFunction_MathFloatLess", "LatchLessL", (300, 1250))
    lsR = add_unit("/Script/RigVM.RigVMFunction_MathFloatLess", "LatchLessR", (300, 1550))
    seL = add_unit("/Script/RigVM.RigVMFunction_MathVectorSelectBool", "LatchSelL", (550, 1100))
    seR = add_unit("/Script/RigVM.RigVMFunction_MathVectorSelectBool", "LatchSelR", (550, 1400))
    tcL = add_unit("/Script/RigVM.RigVMFunction_MathTransformTransformVector", "LatchToCompL", (550, 1250))
    tcR = add_unit("/Script/RigVM.RigVMFunction_MathTransformTransformVector", "LatchToCompR", (550, 1550))

    # 생성된 노드 핀 이름 실측
    def pins_of(nodepath):
        for n in g.get_nodes():
            if str(n.get_node_path()) == nodepath:
                return [str(p.get_name()) for p in n.get_pins()]
        return []
    log["pin_names"] = {"inv": pins_of(inv), "twL": pins_of(twL), "lsL": pins_of(lsL), "seL": pins_of(seL)}

    def link(a, b):
        ok = c.add_link(a, b)
        step(("LINK OK " if ok else "LINK FAIL ") + a + " -> " + b)

    def setdef(pin, val):
        ok = c.set_pin_default_value(pin, val, False)
        step(("DEF OK " if ok else "DEF FAIL ") + pin + " = " + val)

    # 2) 데이터 배선 — L
    link("VariableNode_5.Value", inv + ".Value")
    link("VariableNode_5.Value", twL + ".Transform")
    link("RigVMFunction_MathVectorSub_1.Result", twL + ".Vector")
    link("VariableNode_4.Value", lsL + ".A")          # HandPinAlphaL
    setdef(lsL + ".B", "0.5")
    link(lsL + ".Result", seL + ".Condition")
    link(twL + ".Result", seL + ".IfTrue")
    link("VariableNode_1.Value", seL + ".IfFalse")     # Get HandTargetL (유지값)
    link(seL + ".Result", "VariableNode_6.Value")      # Set HandTargetL
    link(inv + ".Result", tcL + ".Transform")
    link("VariableNode_1.Value", tcL + ".Vector")
    # Lerp.B 재배선
    c.break_link("VariableNode_1.Value", "RigVMFunction_MathVectorLerp.B")
    step("broke VariableNode_1 -> Lerp.B")
    link(tcL + ".Result", "RigVMFunction_MathVectorLerp.B")

    # 3) 데이터 배선 — R
    link("VariableNode_5.Value", twR + ".Transform")
    link("RigVMFunction_MathVectorSub_2.Result", twR + ".Vector")
    link("VariableNode_3.Value", lsR + ".A")          # HandPinAlphaR
    setdef(lsR + ".B", "0.5")
    link(lsR + ".Result", seR + ".Condition")
    link(twR + ".Result", seR + ".IfTrue")
    link("VariableNode_2.Value", seR + ".IfFalse")
    link(seR + ".Result", "VariableNode_7.Value")
    link(inv + ".Result", tcR + ".Transform")
    link("VariableNode_2.Value", tcR + ".Vector")
    c.break_link("VariableNode_2.Value", "RigVMFunction_MathVectorLerp_1.B")
    step("broke VariableNode_2 -> Lerp_1.B")
    link(tcR + ".Result", "RigVMFunction_MathVectorLerp_1.B")

    # 4) exec 체인 끝 찾기 → Set 2개 삽입
    exec_nodes = {}
    for n in g.get_nodes():
        nm = str(n.get_node_path())
        for p in n.get_pins():
            if str(p.get_cpp_type()) == "FRigVMExecuteContext":
                outs = []
                for l in p.get_links():
                    src = str(l.get_source_pin().get_pin_path())
                    tgt = str(l.get_target_pin().get_pin_path())
                    if src.startswith(nm + "."):
                        outs.append(tgt)
                if nm not in exec_nodes:
                    exec_nodes[nm] = []
                exec_nodes[nm] += outs
    log["exec_map"] = exec_nodes
    # 체인 끝 = exec 아웃링크가 없는 exec 노드 (Begin 제외, 신규 Set 제외)
    tail = None
    for nm, outs in exec_nodes.items():
        if nm in ("VariableNode_6", "VariableNode_7"):
            continue
        if "BeginExecution" in nm:
            continue
        if len(outs) == 0:
            tail = nm
    step("exec tail = " + str(tail))
    if tail:
        # tail의 exec 핀 이름 찾기
        tailpin = None
        for n in g.get_nodes():
            if str(n.get_node_path()) == tail:
                for p in n.get_pins():
                    if str(p.get_cpp_type()) == "FRigVMExecuteContext":
                        tailpin = str(p.get_name())
        link(tail + "." + tailpin, "VariableNode_6.ExecuteContext")
        link("VariableNode_6.ExecuteContext", "VariableNode_7.ExecuteContext")

    # 5) 리컴파일 + 저장
    bp.recompile_vm()
    step("recompiled")
    saved = unreal.EditorAssetLibrary.save_asset(CR, only_if_is_dirty=False)
    log["saved"] = bool(saved)
except Exception:
    import traceback
    log["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(log, fp, indent=1)
print("CR_LATCH_DONE")
