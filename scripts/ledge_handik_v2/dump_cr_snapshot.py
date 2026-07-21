# CR 전체 그래프 스냅샷 백업 (read-only) — 발목 로컬 보존 개조 전 안전망 2026-07-21
# 출력: cr_snapshot_<타임스탬프없음>.json  {node: {struct, pins:[{pin,type,dir,default,links}]}}
import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/cr_snapshot_pre_ankle.json"
CR = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_CtrlRig_LedgeDangle"
res = {"asset": CR, "nodes": {}, "variables": []}
try:
    bp = unreal.load_asset(CR)
    for v in bp.get_member_variables():
        try:
            res["variables"].append({"name": str(v.name), "type": str(v.cpp_type)})
        except Exception:
            res["variables"].append({"name": str(v.name)})
    c = bp.get_controller_by_name("RigVMModel") or bp.get_controller()
    g = c.get_graph()
    for n in g.get_nodes():
        nm = str(n.get_node_path())
        pins = []

        # ⚠ 서브핀 필수: Transform 변수의 링크는 Value.Rotation 같은 서브핀에 붙는다.
        #   get_pins() 만 보면 그 링크가 통째로 안 보여서 도달성 분석이 살아있는 노드를 '죽음'으로 오판한다
        #   (2026-07-21 AnkleRel 체인 오탐 — 그대로 지웠으면 회전 보존이 깨질 뻔했음)
        def walk(p, prefix=""):
            name = prefix + str(p.get_name())
            links = []
            for l in p.get_links():
                links.append(str(l.get_opposite_pin(p).get_pin_path()))
            pins.append({"pin": name, "type": str(p.get_cpp_type()),
                         "dir": str(p.get_direction()), "default": str(p.get_default_value())[:120],
                         "links": links})
            try:
                for sp in p.get_sub_pins():
                    walk(sp, name + ".")
            except Exception:
                pass

        for p in n.get_pins():
            walk(p)
        try:
            st = n.get_script_struct()
            stn = str(st.get_name()) if st else ""
        except Exception:
            stn = ""
        try:
            pos = n.get_position()
            xy = [round(pos.x, 1), round(pos.y, 1)]
        except Exception:
            xy = None
        res["nodes"][nm] = {"struct": stn, "pos": xy, "pins": pins}
except Exception:
    import traceback
    res["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(res, fp, indent=1)
print("CR_SNAPSHOT_DONE nodes=%d -> %s" % (len(res["nodes"]), OUT))
