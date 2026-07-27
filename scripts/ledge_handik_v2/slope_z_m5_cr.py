# 경사 Z보정 M5 — CR 펠비스 리프트 삽입 (2026-07-24, 에디터 콘솔/run_python용)
# pelvisFinal = (기존 MathVectorAdd.Result) + (0,0, PelvisSlopeLift × Weight1.0)
# 전제: 유저가 PelvisSlopeLift(float) 변수 + Get 노드 수동 배치 완료
import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/slopez_cr.json"
CR = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_CtrlRig_LedgeDangle"
log = {"steps": []}


def step(m):
    log["steps"].append(str(m))
    print(m)


try:
    bp = unreal.load_asset(CR)
    c = bp.get_controller_by_name("RigVMModel") or bp.get_controller()
    g = c.get_graph()

    # 유저 배치 Get 노드 탐색
    var_node = None
    for n in g.get_nodes():
        try:
            if n.get_variable_name() == "PelvisSlopeLift" and n.is_getter():
                var_node = str(n.get_node_path())
        except Exception:
            pass
    assert var_node, "PelvisSlopeLift Get 노드 미발견 — 수동 배치 확인"
    step("var get node: " + var_node)

    # 기존 링크 전제 확인
    tgt_pin = None
    for n in g.get_nodes():
        if str(n.get_node_path()) == "RigUnit_SetTranslation":
            for p in n.get_pins():
                if str(p.get_name()) == "Value":
                    links = [str(l.get_opposite_pin(p).get_pin_path()) for l in p.get_links()]
                    step("SetTranslation.Value <- " + json.dumps(links))
                    assert links == ["RigVMFunction_MathVectorAdd.Result"], "전제 링크 불일치"

    def add_unit(path, name, pos):
        n = c.add_unit_node_from_struct_path(path, "Execute", unreal.Vector2D(pos[0], pos[1]), name)
        assert n is not None, "add fail " + name
        step("created " + name)
        return str(n.get_node_path())

    nMul = add_unit("/Script/RigVM.RigVMFunction_MathFloatMul", "SlopeLiftWeight", (600, 1500))
    nMk = add_unit("/Script/RigVM.RigVMFunction_MathVectorMake", "SlopeLiftMake", (750, 1500))
    nAdd = add_unit("/Script/RigVM.RigVMFunction_MathVectorAdd", "SlopeLiftAdd", (900, 1500))

    def link(a, b):
        ok = c.add_link(a, b)
        step(("LINK OK " if ok else "LINK FAIL ") + a + " -> " + b)
        assert ok, "link fail"

    def setdef(pin, val):
        c.set_pin_default_value(pin, val, False)
        step("DEF " + pin + " = " + val)

    link(var_node + ".Value", nMul + ".A")
    setdef(nMul + ".B", "1.000000")
    setdef(nMk + ".X", "0.000000")
    setdef(nMk + ".Y", "0.000000")
    link(nMul + ".Result", nMk + ".Z")
    link("RigVMFunction_MathVectorAdd.Result", nAdd + ".A")
    link(nMk + ".Result", nAdd + ".B")
    c.break_link("RigVMFunction_MathVectorAdd.Result", "RigUnit_SetTranslation.Value")
    step("broke Add -> SetTranslation")
    link(nAdd + ".Result", "RigUnit_SetTranslation.Value")

    bp.recompile_vm()
    step("recompiled")
    saved = unreal.EditorAssetLibrary.save_asset(CR, only_if_is_dirty=False)
    log["saved"] = bool(saved)
    step("saved=" + str(saved))
except Exception:
    import traceback
    log["error"] = traceback.format_exc()
    print(log["error"])

with open(OUT, "w") as fp:
    json.dump(log, fp, indent=1)
print("SLOPEZ_CR_DONE")
