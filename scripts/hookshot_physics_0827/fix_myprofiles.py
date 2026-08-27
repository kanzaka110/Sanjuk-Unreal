# -*- coding: utf-8 -*-
"""프로파일을 정본(MyProfiles)에 재작성 (2026-08-27)

배경: 처음에 `Profiles` 에 썼는데 그쪽은 파생/병합본이라 에디터 디테일 패널에 안 뜬다.
      LedgeDangle / Kinematic 원본이 `MyProfiles` 에 있으므로 그쪽이 정본.

작업:
  1) MyProfiles["HookshotAir"] 신규 (Spine + LegLeft + LegRight, Simulated)
  2) MyProfiles["Kinematic"] 에 Spine 복귀 항목 추가 (Control + Modifier 양쪽)
     -> 기존 LegLeft/LegRight 는 실측 원문 그대로 복제하므로 렛지 동작 불변

phase: dry | apply
"""
import json
import sys
import urllib.request

MCP = "http://127.0.0.1:9316/mcp"
ASSET = "/Game/Art/Character/PC/PC_01/Body/PC_01_Body_001/PC_01_Body_001_PhysicControl"
ROOT = "MyProfiles"


def call(tool, args, timeout=180):
    b = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
         "params": {"name": tool, "arguments": args}}
    r = json.load(urllib.request.urlopen(
        urllib.request.Request(MCP, json.dumps(b).encode(),
                               {"Content-Type": "application/json"}), timeout=timeout))
    res = r["result"]
    t = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(t[:600])
    try:
        return json.loads(t)
    except Exception:
        return {"raw": t}


def read(path, fields):
    return call("editor_query", {"action": "list_array_elements", "asset_path": ASSET,
                                 "array_path": path, "fields": fields})


def write(path, value, dry):
    return call("blueprint_query", {"action": "set_property_at_path", "asset_path": ASSET,
                                    "path": path, "value": value,
                                    "create_missing_keys": True, "strict": True,
                                    "dry_run": dry})


def elems(path):
    """[(Name, Data원문), ...]"""
    t = read(path, ["Name", "Data"])
    return [(e["fields"]["Name"], e["fields"]["Data"]) for e in t["elements"]]


def lit(name, data):
    return '(Name="%s",Data=%s)' % (name, data)


def main():
    dry = (sys.argv[1] if len(sys.argv) > 1 else "dry") == "dry"

    # --- 템플릿: LedgeDangle(Simulated) / Kinematic(복귀) 원문에서 가져온다 -----
    ld_ctrl = dict(elems("%s[LedgeDangle].ControlUpdates" % ROOT))
    ld_mod = dict(elems("%s[LedgeDangle].ModifierUpdates" % ROOT))
    kin_ctrl = elems("%s[Kinematic].ControlUpdates" % ROOT)
    kin_mod = elems("%s[Kinematic].ModifierUpdates" % ROOT)

    leg_ctrl = ld_ctrl["ParentSpace_LegLeft"]
    leg_mod = ld_mod["LegLeft"]

    # Spine 용 파생: 다리보다 단단하게(6.0) + 블렌드 낮게(0.5)  ⚠추정 초기값
    spine_ctrl = leg_ctrl.replace("AngularStrength=3.000000", "AngularStrength=6.000000")
    spine_mod = leg_mod.replace("PhysicsBlendWeight=0.700000", "PhysicsBlendWeight=0.500000")
    assert "AngularStrength=6.000000" in spine_ctrl, "Spine Strength 치환 실패"
    assert "PhysicsBlendWeight=0.500000" in spine_mod, "Spine BlendWeight 치환 실패"

    # --- 1) HookshotAir 신규 ------------------------------------------------
    profile = ("(ControlUpdates=(%s,%s,%s),ControlMultiplierUpdates=(),ModifierUpdates=(%s,%s,%s))" % (
        lit("ParentSpace_Spine", spine_ctrl),
        lit("ParentSpace_LegLeft", leg_ctrl),
        lit("ParentSpace_LegRight", leg_ctrl),
        lit("Spine", spine_mod),
        lit("LegLeft", leg_mod),
        lit("LegRight", leg_mod)))
    out = write("%s[HookshotAir]" % ROOT, profile, dry)
    print("1) HookshotAir:", "created_missing_key=%s" % out.get("created_missing_key", "-"),
          "| dry" if dry else "| applied")

    # --- 2) Kinematic 에 Spine 복귀 항목 ------------------------------------
    kin_ctrl_tmpl = kin_ctrl[0][1]
    kin_mod_tmpl = kin_mod[0][1]
    if "ParentSpace_Spine" not in [n for n, _ in kin_ctrl]:
        v = [lit(n, d) for n, d in kin_ctrl] + [lit("ParentSpace_Spine", kin_ctrl_tmpl)]
        write("%s[Kinematic].ControlUpdates" % ROOT, v, dry)
        print("2a) Kinematic.ControlUpdates += ParentSpace_Spine")
    else:
        print("2a) skip (이미 있음)")
    if "Spine" not in [n for n, _ in kin_mod]:
        v = [lit(n, d) for n, d in kin_mod] + [lit("Spine", kin_mod_tmpl)]
        write("%s[Kinematic].ModifierUpdates" % ROOT, v, dry)
        print("2b) Kinematic.ModifierUpdates += Spine")
    else:
        print("2b) skip (이미 있음)")

    if dry:
        return
    # --- 검증 ---------------------------------------------------------------
    print("--- 검증 (%s) ---" % ROOT)
    for prof in ["HookshotAir", "LedgeDangle", "Kinematic"]:
        for arr in ["ControlUpdates", "ModifierUpdates"]:
            t = read("%s[%s].%s" % (ROOT, prof, arr),
                     ["Name", "Data.MovementType", "Data.PhysicsBlendWeight", "Data.AngularStrength"])
            rows = []
            for e in t["elements"]:
                f = e["fields"]
                v = [x for x in (f.get("Data.MovementType"), f.get("Data.PhysicsBlendWeight"),
                                 f.get("Data.AngularStrength")) if x and "unresolved" not in x]
                rows.append("%s%s" % (f["Name"], v))
            print("  %-12s %-16s %s" % (prof, arr, rows))


if __name__ == "__main__":
    main()
