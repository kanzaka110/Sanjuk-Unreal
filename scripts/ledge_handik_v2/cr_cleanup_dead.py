# CR 죽은 노드 제거 (2026-07-21) — 왼손 구 이펙터 잔재 + 고아 knot
#
# 대상 근거: cr_reachability.py 도달성 분석 (서브핀 포함 덤프 기준).
#   왼손은 ReachSubL.A <- RerouteNode_2 로 갈아탔고 구 Lerp 클러스터가 통째로 고아가 됨.
#   ⚠ 오른손 RigVMFunction_MathVectorLerp_1 은 ReachSubR 이 소비 중 — 절대 건드리지 않는다.
#   ⚠ EdGraphNode_Comment_* 는 주석이라 유지. CR 변수도 유지(ABP AnimGraph 핀으로 노출돼 있을 수 있음).
#
# 안전장치: 삭제 직전 매번 그래프 재조회 → 출력 링크가 '삭제대상 밖'으로 가면 중단.
#   (README v6: 스테일 스냅샷 스플라이스로 exec 체인 절단낸 사고 이력)
import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/cr_cleanup_dead.json"
CR = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_CtrlRig_LedgeDangle"
TARGETS = ["RigVMFunction_MathVectorLerp", "RigVMFunction_MathVectorSub_1", "W2RL",
           "RigUnit_GetTransform_1", "VariableNode_1", "VariableNode_4",
           "RerouteNode", "RerouteNode_3", "RerouteNode_4", "RerouteNode_7"]
log = {"removed": [], "skipped": [], "steps": []}
TSET = set(TARGETS)
try:
    bp = unreal.load_asset(CR)
    c = bp.get_controller_by_name("RigVMModel") or bp.get_controller()

    def outgoing(node):
        """이 노드 출력이 향하는 (삭제대상 밖) 노드들"""
        ext = []
        for p in node.get_pins():
            stack = [p]
            while stack:
                q = stack.pop()
                try:
                    stack.extend(q.get_sub_pins())
                except Exception:
                    pass
                for l in q.get_links():
                    src = l.get_source_pin()
                    if str(src.get_pin_path()).split(":")[-1].split(".")[0] != str(node.get_node_path()):
                        continue  # 이 노드가 소스인 링크만 = 출력
                    tgt = str(l.get_target_pin().get_pin_path()).split(":")[-1].split(".")[0]
                    if tgt not in TSET:
                        ext.append(tgt)
        return ext

    for name in TARGETS:
        g = c.get_graph()                      # ★ 매번 재조회
        n = g.find_node_by_name(name)
        if n is None:
            log["skipped"].append({name: "not found"})
            continue
        ext = outgoing(n)
        if ext:
            log["skipped"].append({name: "살아있는 소비자 있음: %s" % sorted(set(ext))})
            continue
        try:
            c.remove_node(n)
            log["removed"].append(name)
        except Exception as e:
            try:
                c.remove_node_by_name(name)
                log["removed"].append(name + " (by_name)")
            except Exception as e2:
                log["skipped"].append({name: "remove fail %s / %s" % (repr(e)[:60], repr(e2)[:60])})

    bp.recompile_vm()
    log["steps"].append("recompiled")
    log["node_count_after"] = len(c.get_graph().get_nodes())
    log["saved"] = bool(unreal.EditorAssetLibrary.save_asset(CR, only_if_is_dirty=False))
except Exception:
    import traceback
    log["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(log, fp, indent=1, ensure_ascii=False)
print("CR_CLEANUP_DONE removed=%d skipped=%d" % (len(log["removed"]), len(log["skipped"])))
