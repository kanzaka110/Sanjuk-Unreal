# -*- coding: utf-8 -*-
"""렛지 RotateRootBone을 컨트롤릭 앞으로 이동 (2026-08-11)

배경: 8/10 요 스무딩 빌드(ledge_yaw_smooth_build.py phase_anim)가 RotateRootBone을
  CR -> Root 사이에 삽입했다. CR은 손/발을 월드 타깃(W2RL/W2RR = ToRigSpace_Location)에
  고정하는데, 그 뒤 RotateRootBone이 루트째 LedgeYawSmoothOffset 만큼 포즈를 회전시켜
  고정해둔 손이 렛지에서 그 각도만큼 떨어져 나간다.
  offset은 코너에서 튀었다가 FInterpTo(12)로 감쇠 -> 방향 전환 직후 0.3~0.5s만 깨짐(간헐적).

수정: 월드공간 IK는 항상 마지막. 순서를 뒤집는다.
  before: TwoWayBlend_0 -> CR_11 -> RRB_1 -> Root
  after : TwoWayBlend_0 -> RRB_1 -> CR_11 -> Root
  노드 신규 생성 0개, 와이어 3개 재배선.
"""
import json
import sys
import urllib.request

MCP = "http://localhost:9316/mcp"
BP = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_AnimLayer_Ledge"
G = "Ledge"

BLEND = "AnimGraphNode_TwoWayBlend_0"
CR = "AnimGraphNode_ControlRig_11"
RRB = "AnimGraphNode_RotateRootBone_1"
ROOT = "AnimGraphNode_Root_0"


def call(tool, action, params, timeout=300):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(MCP, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:500])
    try:
        return json.loads(txt)
    except Exception:
        return {"raw": txt}


def links(node_id):
    d = call("blueprint_query", "get_node_details",
             {"asset_path": BP, "graph_name": G, "node_id": node_id})
    return {p["name"]: p.get("connected_to") or [] for p in d["pins"]}


def disconnect(sn, sp, tn, tp):
    call("blueprint_query", "disconnect_pins",
         {"asset_path": BP, "graph_name": G,
          "source_node": sn, "source_pin": sp, "target_node": tn, "target_pin": tp})
    print("  - %s.%s -/-> %s.%s" % (sn, sp, tn, tp))


def connect(pairs):
    rc = call("blueprint_query", "connect_pins_bulk",
              {"asset_path": BP, "graph_name": G, "connections": [
                  {"source_node": a, "source_pin": b, "target_node": c, "target_pin": d}
                  for a, b, c, d in pairs]})
    fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
    for fl in fails:
        print("  !! conn fail:", json.dumps(fl, ensure_ascii=False)[:250])
    for a, b, c, d in pairs:
        print("  + %s.%s --> %s.%s" % (a, b, c, d))
    return len(fails)


def preflight():
    """현재 배선이 예상한 8/10 상태인지 확인. 다르면 중단."""
    cr = links(CR)
    rrb = links(RRB)
    root = links(ROOT)
    assert cr["Source"] == ["%s.Pose" % BLEND], "CR.Source 배선 상이: %s" % cr["Source"]
    assert cr["Pose"] == ["%s.BasePose" % RRB], "CR.Pose 배선 상이: %s" % cr["Pose"]
    assert rrb["BasePose"] == ["%s.Pose" % CR], "RRB.BasePose 배선 상이: %s" % rrb["BasePose"]
    assert root["Result"] == ["%s.Pose" % RRB], "Root.Result 배선 상이: %s" % root["Result"]
    # 요 스무딩 바인딩이 살아있는지 (재배선으로 날아가면 기능 사망)
    b = call("animation_query", "get_anim_node_pin_bindings",
             {"asset_path": BP, "graph_name": G, "node_id": RRB})
    print("[PRE] RRB bindings:", json.dumps(b, ensure_ascii=False)[:300])
    print("[PRE] ok — TwoWayBlend_0 -> CR_11 -> RRB_1 -> Root")


def rewire():
    disconnect(BLEND, "Pose", CR, "Source")
    disconnect(CR, "Pose", RRB, "BasePose")
    disconnect(RRB, "Pose", ROOT, "Result")
    f = connect([
        (BLEND, "Pose", RRB, "BasePose"),
        (RRB, "Pose", CR, "Source"),
        (CR, "Pose", ROOT, "Result"),
    ])
    assert f == 0, "재배선 실패 %d건" % f
    # 노드 위치도 순서에 맞게 (CR pos=[-256,0] 기준 RRB를 그 앞으로)
    call("blueprint_query", "set_node_position",
         {"asset_path": BP, "graph_name": G, "node_id": RRB, "position": [-560, 0]})


def verify():
    cr = links(CR)
    rrb = links(RRB)
    root = links(ROOT)
    assert rrb["BasePose"] == ["%s.Pose" % BLEND], "RRB.BasePose = %s" % rrb["BasePose"]
    assert cr["Source"] == ["%s.Pose" % RRB], "CR.Source = %s" % cr["Source"]
    assert root["Result"] == ["%s.Pose" % CR], "Root.Result = %s" % root["Result"]
    b = call("animation_query", "get_anim_node_pin_bindings",
             {"asset_path": BP, "graph_name": G, "node_id": RRB})
    print("[POST] RRB bindings:", json.dumps(b, ensure_ascii=False)[:300])
    print("[POST] ok — TwoWayBlend_0 -> RRB_1 -> CR_11 -> Root")


def compile_bp():
    r = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
    print("[COMPILE] errors=%s %s" % (
        r.get("error_count"),
        json.dumps(r.get("errors"), ensure_ascii=False)[:400] if r.get("error_count") else ""))
    return r


def save():
    r = call("blueprint_query", "save_asset", {"asset_path": BP})
    print("[SAVE]", json.dumps(r, ensure_ascii=False)[:400])


def phase_all():
    preflight()
    rewire()
    verify()
    compile_bp()


if __name__ == "__main__":
    ph = sys.argv[1] if len(sys.argv) > 1 else "all"
    {"pre": preflight, "all": phase_all, "verify": verify,
     "compile": compile_bp, "save": save}[ph]()
