# 왼손 이펙터 체인 복구 (2026-07-21) — cr_cleanup_dead.py 오삭제 복구
#
# 사고: 도달성 분석기가 Reroute 의 IO 핀을 '입력'으로 취급하지 않아 knot 뒤 체인을 못 따라감
#       → 살아있던 왼손 이펙터 클러스터를 dead 로 오판하고 삭제.
#       끊긴 경로: (삭제됨) -> RerouteNode_3 -> RerouteNode_2 -> ReachSubL.A -> ... -> 왼손 TwoBoneIK.Effector
#
# 원본 구조 (cr_snapshot_pre_ankle.BACKUP.json):
#   Sub_1.A <- RigUnit_GetTransform_1.Transform.Translation
#   Sub_1.B <- RerouteNode.Value (<- RigVMFunction_MathVectorClampLength.Result)   ※ knot 생략하고 직결
#   Lerp.A  <- Sub_1.Result / Lerp.B <- W2RL.Global / Lerp.T <- Get HandPinAlphaL
#   W2RL.Value <- Get HandTargetL
#   Lerp.Result -> RerouteNode_3.Value
#
# 변수 Get 2개(HandTargetL / HandPinAlphaL)는 CR 에서 스크립트 생성이 크래시 이력이 있어 유저 수동.
#   미연결 상태에서도 Lerp.T=0 → 왼손 IK 알파 0 = 애님 그대로(안전) 로 복구된다.
import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/cr_restore_lefthand.json"
CR = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_CtrlRig_LedgeDangle"
CLAMP_SRC = "RigVMFunction_MathVectorClampLength"
log = {"created": [], "links": [], "steps": []}
try:
    bp = unreal.load_asset(CR)
    c = bp.get_controller_by_name("RigVMModel") or bp.get_controller()
    g = c.get_graph()

    for nm in ("RigUnit_GetTransform_1", CLAMP_SRC, "RerouteNode_3", "ReachSubL"):
        if g.find_node_by_name(nm) is None:
            raise RuntimeError("복구 앵커 없음: " + nm)

    def add_unit(path, name, pos):
        n = c.add_unit_node_from_struct_path(path, "Execute", unreal.Vector2D(pos[0], pos[1]), name)
        if n is None:
            raise RuntimeError("add fail " + name)
        log["created"].append(str(n.get_node_path()))
        return str(n.get_node_path())

    def link(a, b):
        try:
            ok = c.add_link(a, b)
            log["links"].append(("OK " if ok else "FAIL ") + a + " -> " + b)
        except Exception as e:
            log["links"].append("ERR " + a + " -> " + b + " : " + repr(e)[:110])

    sub = add_unit("/Script/RigVM.RigVMFunction_MathVectorSub", "RestoreHandSubL", (-400, 112))
    w2r = add_unit("/Script/ControlRig.RigUnit_ToRigSpace_Location", "W2RL", (-400, 224))
    lrp = add_unit("/Script/RigVM.RigVMFunction_MathVectorLerp", "RestoreHandLerpL", (-224, 192))

    link("RigUnit_GetTransform_1.Transform.Translation", sub + ".A")
    link(CLAMP_SRC + ".Result", sub + ".B")          # 구 RerouteNode 는 생략하고 직결
    link(sub + ".Result", lrp + ".A")
    link(w2r + ".Global", lrp + ".B")
    # Lerp.T 는 미연결 = 0 (왼손 IK off, 애님 그대로) — 유저가 Get HandPinAlphaL 연결하면 원복
    c.set_pin_default_value(lrp + ".T", "0.000000", False)
    try:
        c.break_all_links("RerouteNode_3.Value", True)
    except Exception:
        pass
    link(lrp + ".Result", "RerouteNode_3.Value")

    bp.recompile_vm()
    log["steps"].append("recompiled")
    log["saved"] = bool(unreal.EditorAssetLibrary.save_asset(CR, only_if_is_dirty=False))
    log["todo_manual"] = ["Get HandTargetL -> %s.Value" % w2r, "Get HandPinAlphaL -> %s.T" % lrp]
except Exception:
    import traceback
    log["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(log, fp, indent=1, ensure_ascii=False)
print("CR_RESTORE_LEFTHAND_DONE err=%s" % ("error" in log))
