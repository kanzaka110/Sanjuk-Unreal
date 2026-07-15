# CR 발 IK 변수 배선 — 유저가 CR에 변수 4개(FootTargetL/R Vector, FootAlphaL/R Float, public)
# + Get 노드 4개를 만든 뒤 실행. FootLerpL/R.B<-FootTarget, .T<-FootAlpha 연결 + recompile + save.
import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/cr_foot_wire.json"
CR = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_CtrlRig_LedgeDangle"
log = {"steps": []}


def step(m):
    log["steps"].append(str(m))


try:
    bp = unreal.load_asset(CR)
    c = bp.get_controller_by_name("RigVMModel") or bp.get_controller()
    model = bp.get_model_by_name("RigVMModel") or bp.get_default_model()

    # 변수 Get 노드 탐색 (variable name -> node path)
    var_nodes = {}
    for n in model.get_nodes():
        try:
            vname = str(n.get_variable_name())
        except Exception:
            continue
        if vname in ("FootTargetL", "FootTargetR", "FootAlphaL", "FootAlphaR"):
            if n.is_getter() if hasattr(n, "is_getter") else True:
                var_nodes[vname] = str(n.get_node_path())
    step("found: " + json.dumps(var_nodes))
    missing = [v for v in ("FootTargetL", "FootTargetR", "FootAlphaL", "FootAlphaR") if v not in var_nodes]
    if missing:
        raise RuntimeError("Get 노드 미발견: %s — CR에 변수+Get 노드 생성 필요" % missing)

    def link(a, b):
        try:
            ok = c.add_link(a, b)
            step(("LINK OK " if ok else "LINK FAIL ") + a + " -> " + b)
        except Exception as e:
            step("LINK ERR " + a + " -> " + b + " : " + repr(e)[:100])

    for side in ("L", "R"):
        link(var_nodes["FootTarget" + side] + ".Value", "FootLerp%s.B" % side)
        link(var_nodes["FootAlpha" + side] + ".Value", "FootLerp%s.T" % side)
        # Weight도 알파로 게이트 — 알파0이면 유닛 완전 오프 (폴벡터 무릎 강제 차단, 디폴트 0 대체)
        link(var_nodes["FootAlpha" + side] + ".Value", "FootIK%s.Weight" % side)

    bp.recompile_vm()
    step("recompiled")
    saved = unreal.EditorAssetLibrary.save_asset(CR, only_if_is_dirty=False)
    log["saved"] = bool(saved)
except Exception:
    import traceback
    log["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(log, fp, indent=1)
print("CR_FOOT_WIRE_DONE")
