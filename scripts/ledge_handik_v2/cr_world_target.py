# CR 손 타깃 월드공간화 — HandTargetL/R(이제 월드값 수신)와 Lerp.B 사이에 ToRigSpace_Location 삽입
# 목적: ABP측 1틱 스테일 M2W 변환 제거 (정지 에지 1틱 오버슈트 근본 수정)
# 롤백: W2RL/W2RR 삭제 + VariableNode_1.Value->Lerp.B, VariableNode_2.Value->Lerp_1.B 재링크
import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/cr_world_target.json"
CR = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_CtrlRig_LedgeDangle"
log = {"steps": []}


def step(m):
    log["steps"].append(str(m))


try:
    bp = unreal.load_asset(CR)
    c = bp.get_controller_by_name("RigVMModel") or bp.get_controller()

    def add_unit(path, name, pos):
        n = c.add_unit_node_from_struct_path(path, "Execute", unreal.Vector2D(pos[0], pos[1]), name)
        if n is None:
            raise RuntimeError("add fail " + name)
        step("created " + name + " pins=" + ",".join(str(p.get_name()) for p in n.get_pins()))
        return str(n.get_node_path())

    def link(a, b, brk=False):
        if brk:
            try:
                c.break_all_links(b, True)
            except Exception:
                pass
        ok = c.add_link(a, b)
        step(("LINK OK " if ok else "LINK FAIL ") + a + " -> " + b)
        if not ok:
            raise RuntimeError("link fail " + a + " -> " + b)

    existing = {str(n.get_node_path()) for n in c.get_graph().get_nodes()}
    for name, src, dst, y in (("W2RL", "VariableNode_1", "RigVMFunction_MathVectorLerp", 300),
                              ("W2RR", "VariableNode_2", "RigVMFunction_MathVectorLerp_1", 500)):
        if name in existing:
            n = name
            step("reuse " + name)
        else:
            n = add_unit("/Script/ControlRig.RigUnit_ToRigSpace_Location", name, (-1200, y))
        try:
            c.break_all_links(n + ".Value", True)
        except Exception:
            pass
        link(src + ".Value", n + ".Value")
        link(n + ".Global", dst + ".B", brk=True)

    bp.recompile_vm()
    step("recompiled")
    log["saved"] = bool(unreal.EditorAssetLibrary.save_asset(CR, only_if_is_dirty=False))
except Exception:
    import traceback
    log["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(log, fp, indent=1)
print("CR_WORLD_TARGET_DONE")
