# -*- coding: utf-8 -*-
"""Step 1-2 (XGen Convert to Interactive + Cache round-trip) ground-truth introspection.

read-only. 씬 변경 없음. 결과를 dumps/maya_introspect_step12.json 으로 write.
실행: maya_send.py py "exec(open('.../introspect_xgen_step12.py').read())"
"""
import json
import os

import maya.cmds as cmds

out = {
    "maya_version": "",
    "node_inventory": {},
    "whatis": {},
    "menu_commands": [],
    "script_editor_history_tail": [],
    "history_hits": [],
    "errors": [],
}

try:
    out["maya_version"] = cmds.about(version=True)
except Exception as e:  # noqa: BLE001
    out["errors"].append("about: {}".format(e))

# 1. 현재 groom 관련 노드 인벤토리 (변환 결과 파악)
for t in (
    "xgmPalette",
    "xgmDescription",
    "xgmSubdPatch",
    "xgmSplineDescription",
    "xgmSplineBase",
    "xgmSplineCache",
    "xgmGuide",
    "nurbsCurve",
    "mesh",
):
    try:
        nodes = cmds.ls(type=t) or []
        out["node_inventory"][t] = {"count": len(nodes), "sample": nodes[:20]}
    except Exception as e:  # noqa: BLE001
        out["errors"].append("ls {}: {}".format(t, e))

# 2. 후보 명령 존재 여부 (whatIs — 추측 명령이 실제로 존재하는지 검증)
for c in (
    "xgmSplineCache",
    "xgmCreateCurvesFromGuides",
    "xgmConvertToInteractiveGroom",
    "xgmInteractiveBaseFromGroom",
    "xgmCreateDescription",
    "xgmSelectedGuides",
    "xgmFindAttachment",
    "xgmPushToArchive",
    "xgmExportToAlembic",
    "xgmModifierCache",
    "xgmNullRender",
):
    try:
        out["whatis"][c] = cmds.whatIs(c)
    except Exception as e:  # noqa: BLE001
        out["whatis"][c] = "ERR: {}".format(e)

# 3. XGen 메뉴 아이템의 실제 -command 문자열 (Convert/Interactive/Cache/Guide/Curve)
try:
    for mi in cmds.lsUI(type="menuItem") or []:
        try:
            lbl = cmds.menuItem(mi, q=True, label=True) or ""
        except Exception:  # noqa: BLE001
            continue
        low = lbl.lower()
        if any(
            k in low
            for k in ("interactive", "convert", "cache", "curves from guides", "guide")
        ):
            cmd = ""
            try:
                cmd = cmds.menuItem(mi, q=True, command=True) or ""
            except Exception:  # noqa: BLE001
                cmd = "<no command>"
            out["menu_commands"].append(
                {"item": mi, "label": lbl, "command": str(cmd)[:3000]}
            )
except Exception as e:  # noqa: BLE001
    out["errors"].append("menu scan: {}".format(e))

# 4. Script Editor history — 방금 수동 작업의 echo된 실제 명령
KEYS = (
    "xgm",
    "Interactive",
    "interactive",
    "Cache",
    "cache",
    "AbcExport",
    "AbcImport",
    "CreateCurves",
    "Convert",
    "convert",
    "guide",
    "Guide",
    "splineDescription",
)
try:
    reporters = cmds.lsUI(type="cmdScrollFieldReporter") or []
    for rep in reporters:
        try:
            txt = cmds.cmdScrollFieldReporter(rep, q=True, text=True) or ""
        except Exception as e:  # noqa: BLE001
            out["errors"].append("reporter {}: {}".format(rep, e))
            continue
        out["script_editor_history_tail"].append(
            {"reporter": rep, "len": len(txt), "tail": txt[-20000:]}
        )
        for line in txt.splitlines():
            if any(k in line for k in KEYS):
                out["history_hits"].append(line.strip()[:500])
except Exception as e:  # noqa: BLE001
    out["errors"].append("reporter scan: {}".format(e))

# dedup history_hits, keep order
_seen = set()
_dedup = []
for h in out["history_hits"]:
    if h and h not in _seen:
        _seen.add(h)
        _dedup.append(h)
out["history_hits"] = _dedup[-400:]

dump_path = "C:/Dev/Sanjuk-Unreal/dumps/maya_introspect_step12.json"
try:
    os.makedirs(os.path.dirname(dump_path), exist_ok=True)
    with open(dump_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("WROTE " + dump_path)
except Exception as e:  # noqa: BLE001
    print("WRITE_FAILED " + str(e))
