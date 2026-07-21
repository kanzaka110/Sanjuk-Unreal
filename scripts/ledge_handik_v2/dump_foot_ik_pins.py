# FootIK 노드(TwoBoneIKSimplePerItem) 전 핀 덤프 — 회전 적용 옵션 핀 존재 확인용 (read-only)
# 발목 꺾임 조사 2026-07-21: 이펙터 회전 강제를 끌 수 있는 핀이 있는지 판정
import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/foot_ik_pins.json"
CR = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_CtrlRig_LedgeDangle"
res = {}
try:
    bp = unreal.load_asset(CR)
    c = bp.get_controller_by_name("RigVMModel") or bp.get_controller()
    g = c.get_graph()
    for n in g.get_nodes():
        nm = str(n.get_node_path())
        if not (nm.startswith("FootIK") or nm.startswith("FootMake") or nm.startswith("FootLerp")):
            continue
        pins = []
        for p in n.get_pins():
            links = []
            for l in p.get_links():
                links.append(str(l.get_opposite_pin(p).get_pin_path()))
            sub = [str(s.get_name()) for s in p.get_sub_pins()] if hasattr(p, "get_sub_pins") else []
            pins.append({"pin": str(p.get_name()),
                         "type": str(p.get_cpp_type()),
                         "dir": str(p.get_direction()),
                         "default": str(p.get_default_value())[:80],
                         "links": links,
                         "sub": sub})
        res[nm] = {"struct": str(n.get_script_struct().get_name()) if hasattr(n, "get_script_struct") and n.get_script_struct() else "?",
                   "pins": pins}
except Exception:
    import traceback
    res["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(res, fp, indent=1)
print("FOOT_IK_PINS_DONE -> " + OUT)
