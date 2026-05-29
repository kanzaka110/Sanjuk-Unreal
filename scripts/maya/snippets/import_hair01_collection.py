"""hair01 컬렉션 강제 import (사용자 승인 — 현 씬에 강제 임포트).

- 프로젝트를 _source 로 설정해 ${PROJECT} 가 데이터 폴더로 해석되게 함.
- before/after 팔레트 + 신규 description 을 결과 JSON 으로 기록.
- multi-statement 라 commandPort 반환 불가 → 결과를 파일로 dump 후 호출측에서 read.
"""
import json
import traceback

import maya.cmds as cmds
import xgenm as xg

XGEN_FILE = "E:/Maya/Evie_GroomHair/evie_hair5_fix2__hair01.xgen"
PROJECT = "E:/Maya/Evie_GroomHair/_source"
OUT = "E:/Maya/Evie_GroomHair/_import_result.json"

result = {}
try:
    cmds.workspace(PROJECT, openWorkspace=True)
    result["project"] = cmds.workspace(q=True, rootDirectory=True)
    result["before_palettes"] = list(xg.palettes())
    result["before_desc_hair01"] = list(xg.descriptions("hair01")) if "hair01" in xg.palettes() else []

    new_pal = xg.importPalette(XGEN_FILE, [], "")
    result["imported_palette"] = new_pal

    result["after_palettes"] = list(xg.palettes())
    if new_pal and new_pal in xg.palettes():
        result["new_descriptions"] = list(xg.descriptions(new_pal))
except Exception as e:  # noqa: BLE001 - 결과 파일에 전체 트레이스백 기록
    result["error"] = repr(e)
    result["traceback"] = traceback.format_exc()

with open(OUT, "w", encoding="utf-8") as f:
    f.write(json.dumps(result, indent=2))
