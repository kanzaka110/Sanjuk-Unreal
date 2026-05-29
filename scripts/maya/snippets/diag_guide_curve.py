"""Guide Curve 생성 실패 진단 — 선택 상태 + 가이드/스플라인 노드 분포 dump.

commandPort echoOutput=false 라 결과 반환 안 됨 → JSON 파일로 write 후 호출측 read.
"""
import json
import traceback

import maya.cmds as cmds

OUT = "E:/Maya/Evie_GroomHair/_diag_guide.json"

r = {}
try:
    # 1) 현재 선택
    sel = cmds.ls(sl=True, long=True) or []
    r["selection_count"] = len(sel)
    r["selection_sample"] = sel[:20]
    # 선택된 것들의 노드 타입
    sel_types = {}
    for s in sel:
        for n in cmds.ls(s, dag=True, long=True) or [s]:
            t = cmds.nodeType(n)
            sel_types[t] = sel_types.get(t, 0) + 1
    r["selection_types"] = sel_types

    # 2) 씬 전체 가이드/스플라인 관련 노드 타입 카운트
    def count(t):
        try:
            return len(cmds.ls(type=t, long=True) or [])
        except Exception:
            return "N/A"

    r["counts"] = {
        "xgmSplineDescription": count("xgmSplineDescription"),
        "xgmSplineBase": count("xgmSplineBase"),
        "xgmSplineGuide": count("xgmSplineGuide"),
        "xgmGuide": count("xgmGuide"),
        "xgmDescription": count("xgmDescription"),
        "xgmPalette": count("xgmPalette"),
        "nurbsCurve": count("nurbsCurve"),
    }

    # 3) Legacy XGen palettes/descriptions
    try:
        import xgenm as xg
        r["legacy_palettes"] = {p: list(xg.descriptions(p)) for p in xg.palettes()}
    except Exception as e:
        r["legacy_palettes_error"] = repr(e)

    # 4) Interactive splineDescription 노드 + 각 desc 의 guide 보유 여부
    spline_descs = cmds.ls(type="xgmSplineDescription", long=True) or []
    desc_info = []
    for d in spline_descs[:30]:
        info = {"node": d}
        # splineDescription 하위 guide 노드 탐색
        guides = cmds.ls(cmds.listRelatives(d, ad=True, f=True) or [], type="xgmSplineGuide") or []
        info["spline_guides_under"] = len(guides)
        desc_info.append(info)
    r["spline_desc_info"] = desc_info
    r["spline_desc_total"] = len(spline_descs)

except Exception as e:  # noqa: BLE001
    r["error"] = repr(e)
    r["traceback"] = traceback.format_exc()

with open(OUT, "w", encoding="utf-8") as f:
    f.write(json.dumps(r, indent=2))
