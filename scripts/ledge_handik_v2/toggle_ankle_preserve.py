# 발목 보존 개조 ON/OFF 토글 — A/B 실측용 (2026-07-21)
# AnkSetRotL/R.Weight 를 0 <-> 1 로 뒤집는다. 0 = 개조 전과 동일 동작(회전 보존 없음).
# 발목 꺾임 vs ball 접지 오차 트레이드오프를 같은 조건에서 비교하기 위한 스위치.
import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/ankle_toggle.json"
CR = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_CtrlRig_LedgeDangle"
log = {}
try:
    bp = unreal.load_asset(CR)
    c = bp.get_controller_by_name("RigVMModel") or bp.get_controller()
    g = c.get_graph()
    cur = None
    for nm in ("AnkSetRotL", "AnkSetRotR"):
        n = g.find_node_by_name(nm)
        if n is None:
            raise RuntimeError("node not found: " + nm)
        for p in n.get_pins():
            if str(p.get_name()) == "Weight":
                cur = float(p.get_default_value() or 0.0)
    new = 0.0 if (cur or 0.0) > 0.5 else 1.0
    for nm in ("AnkSetRotL", "AnkSetRotR"):
        c.set_pin_default_value(nm + ".Weight", "%.6f" % new, False)
    bp.recompile_vm()
    log["prev"] = cur
    log["new"] = new
    log["state"] = "ON (발목 로컬 보존)" if new > 0.5 else "OFF (개조 전과 동일)"
    log["saved"] = bool(unreal.EditorAssetLibrary.save_asset(CR, only_if_is_dirty=False))
except Exception:
    import traceback
    log["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(log, fp, indent=1)
print("ANKLE_TOGGLE -> %s" % log.get("state", log.get("error", "?")))
