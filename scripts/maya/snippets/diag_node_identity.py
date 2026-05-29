"""특정 노드 정체 + 네임스페이스 + 가이드 노드 샘플 진단."""
import json
import traceback

import maya.cmds as cmds

OUT = "E:/Maya/Evie_GroomHair/_diag_node.json"
TARGET = "evie_hair5_fix2:SplineGrp0_Curve_1215_4"

r = {}
try:
    # 네임스페이스
    r["namespaces"] = [n for n in (cmds.namespaceInfo(lon=True, r=True) or [])
                       if n not in ("UI", "shared")]

    # 타겟 노드 정체
    found = cmds.ls(TARGET, long=True) or cmds.ls("*" + TARGET.split(":")[-1], long=True)[:3]
    r["target_query"] = TARGET
    r["target_found"] = found[:5]
    if found:
        node = found[0]
        r["target_type"] = cmds.nodeType(node)
        r["target_parents"] = cmds.listRelatives(node, parent=True, f=True)
        shapes = cmds.listRelatives(node, shapes=True, f=True) or []
        r["target_shapes"] = [(s, cmds.nodeType(s)) for s in shapes]
        # 전체 부모 체인
        chain, cur = [], node
        for _ in range(8):
            p = cmds.listRelatives(cur, parent=True, f=True)
            if not p:
                break
            chain.append((p[0], cmds.nodeType(p[0])))
            cur = p[0]
        r["target_parent_chain"] = chain

    # SplineGrp* 커브 vs GuideCrv* 그룹 개수
    r["count_SplineGrp_curves"] = len(cmds.ls("*SplineGrp*Curve*", long=True) or [])
    r["count_GuideCrv"] = len(cmds.ls("*GuideCrv*", long=True) or [])

    # xgmSplineGuide 샘플 이름
    guides = cmds.ls(type="xgmSplineGuide", long=True) or []
    r["spline_guide_total"] = len(guides)
    r["spline_guide_sample"] = guides[:5]

    # 최상위 그룹(어셈블리) 트리
    tops = cmds.ls(assemblies=True, long=True) or []
    r["top_level"] = tops[:40]

except Exception as e:  # noqa: BLE001
    r["error"] = repr(e)
    r["traceback"] = traceback.format_exc()

with open(OUT, "w", encoding="utf-8") as f:
    f.write(json.dumps(r, indent=2))
