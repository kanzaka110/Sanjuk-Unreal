# -*- coding: utf-8 -*-
"""스윙 좌/중/우 모션 분기 — 챠저 FloatRange 컬럼 추가 (2026-08-27)

승호 지시: "P_Player_HookSwing_Move_Right / _Left 두 모션 추가. 상/중/하 했던것처럼
            좌/중/우로, 정면으로 특정 각도 이상일때 저 모션들이 나오게"

ESBHookshotLandDir 은 UserDefinedEnum 인데 Monolith 에 '기존 enum 에 값 추가' 액션이
없다(create_user_defined_enum 만 있음). 그래서 enum 확장 대신 FloatRange 입력 컬럼을
붙여 좌/중/우를 가른다. 임계각을 챠저 셀에서 바로 조절할 수 있는 이점도 있다.

기존 표 (실측):
  row0~2  Type MatchNotEqual 2 (일반)  LandDir 3/1/2 -> Hook_Move_Forward
  row3    Type MatchEqual    2 (스윙)  LandDir 3     -> HookSwing_Move_Forward
  row4    Type=2                       LandDir 1     -> HookSwing_Move_Down
  row5    Type=2                       LandDir 2     -> HookSwing_Move_Up

추가 후:
  신규 컬럼3 = FloatRange(HookSwingSideAngle)
  row0~2,4,5 : 전범위 (영향 없음)
  row3       : -THRESH ~ +THRESH   (중앙으로 좁힘)
  row6 (신규): -180 ~ -THRESH  -> HookSwing_Move_Left
  row7 (신규): +THRESH ~ 180   -> HookSwing_Move_Right
행 순서에 의존하지 않도록 범위를 배타적으로 나눈다.

phase: column | rows | verify | save | all
"""
import json
import sys
import urllib.request

MCP = "http://127.0.0.1:9316/mcp"
CH = "/Game/Art/Character/PC/PC_01/StateMachine/CustomMove/HookShotMoving"
ANIM = "/Game/Art/Character/PC/PC_01/Animation/Body/Hook/"
THRESH = 30.0          # 좌/우로 갈리는 정면 대비 임계각(도)
WIDE = 99999.0
TYPE_SWING = 2         # ESBHookshotType: Swing (챠저 실측으로 확정)
DIR_FROMSIDE = 3       # ESBHookshotLandDir: FromSide
SWING_COL = 0
DIR_COL = 1
FLOAT_COL = 3          # 추가될 컬럼 인덱스 (기존 0,1 입력 + 2 출력)


def call(action, args, tool="chooser_query", timeout=300):
    a = dict(args)
    a["action"] = action
    b = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
         "params": {"name": tool, "arguments": a}}
    r = json.load(urllib.request.urlopen(
        urllib.request.Request(MCP, json.dumps(b).encode(),
                               {"Content-Type": "application/json"}), timeout=timeout))
    res = r["result"]
    t = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError("%s: %s" % (action, t[:500]))
    try:
        return json.loads(t)
    except Exception:
        return {"raw": t}


def info(cells=False):
    return call("inspect_chooser", {"asset_path": CH, "include_cells": cells})


def do_column():
    o = info()
    if o["column_count"] > 3:
        print("  skip (이미 컬럼 %d개)" % o["column_count"])
        return
    call("add_chooser_column", {"asset_path": CH, "column_kind": "FloatRange",
                                "binding_property": "HookSwingSideAngle"})
    print("  +컬럼 FloatRange (HookSwingSideAngle)")
    # 기존 행 전부 전범위로 열어둔다 (기본값이 0~0 이면 전 행이 매칭 실패한다)
    n = info()["row_count"]
    for r in range(n):
        call("set_chooser_cell", {"asset_path": CH, "column_index": FLOAT_COL,
                                  "row_index": r, "float_min": -WIDE, "float_max": WIDE})
    print("  기존 %d행 전범위(-%g~%g) 설정" % (n, WIDE, WIDE))
    # 스윙 Forward 행만 중앙 구간으로 좁힌다
    call("set_chooser_cell", {"asset_path": CH, "column_index": FLOAT_COL,
                              "row_index": 3, "float_min": -THRESH, "float_max": THRESH})
    print("  row3(스윙 Forward) = %g ~ %g" % (-THRESH, THRESH))


def do_rows():
    o = info(cells=True)
    have = {a["asset"].split(".")[-1] for a in o["referenced_assets"]}
    plan = [("P_Player_HookSwing_Move_Left", -180.0, -THRESH),
            ("P_Player_HookSwing_Move_Right", THRESH, 180.0)]
    for name, lo, hi in plan:
        if name in have:
            print("  skip (이미 있음)", name)
            continue
        call("add_chooser_row", {
            "asset_path": CH,
            "cells": [TYPE_SWING, DIR_FROMSIDE, {"min": lo, "max": hi}],
            "output_psd": ANIM + name,
        })
        print("  +행 %-30s Type=%d Dir=%d  %g ~ %g" % (name, TYPE_SWING, DIR_FROMSIDE, lo, hi))


def do_verify():
    o = info(cells=True)
    assets = {a["row"]: a["asset"].split(".")[-1] for a in o["referenced_assets"]}
    cells = {}
    for c in o["columns"]:
        for cell in (c.get("cells") or []):
            cells.setdefault(cell["row"], {})[c["index"]] = cell
    print("  행수=%d 컬럼수=%d" % (o["row_count"], o["column_count"]))
    for r in sorted(assets):
        c = cells.get(r, {})
        t = c.get(SWING_COL, {})
        d = c.get(DIR_COL, {})
        f = c.get(FLOAT_COL, {})
        rng = ""
        if f:
            rng = "%g~%g" % (f.get("min", 0), f.get("max", 0))
        print("   row%d Type=%s(cmp%s) Dir=%s  범위[%s]  -> %s"
              % (r, t.get("value"), t.get("comparison"), d.get("value"), rng, assets[r]))
    v = call("validate_chooser", {"asset_path": CH})
    print("  validate:", json.dumps(v, ensure_ascii=False)[:200])


def do_save():
    o = call("save_packages", {"packages": [CH]}, tool="editor_query")
    print("  save:", o.get("ok"), o.get("saved"))


PHASES = {"column": do_column, "rows": do_rows, "verify": do_verify, "save": do_save}

if __name__ == "__main__":
    ph = sys.argv[1] if len(sys.argv) > 1 else "all"
    for p in (["column", "rows", "verify", "save"] if ph == "all" else [ph]):
        print("==", p)
        PHASES[p]()
