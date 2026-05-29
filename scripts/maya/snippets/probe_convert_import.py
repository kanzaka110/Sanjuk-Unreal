# -*- coding: utf-8 -*-
"""xgmGroomConvert + XgmSplineCacheImport 시그니처 확정 probe. read-only."""
import json
import os

import maya.cmds as cmds
import maya.mel as mel

out = {"whatis": {}, "help": {}, "errors": []}

for c in ("xgmGroomConvert", "XgmSplineCacheImport", "XgmSplineCacheExport",
          "XgmSplineCacheCreate", "xgmConvertCurveToSpline"):
    try:
        out["whatis"][c] = mel.eval('whatIs "{}"'.format(c))
    except Exception as e:  # noqa: BLE001
        out["whatis"][c] = "ERR: {}".format(e)
    try:
        h = cmds.help(c)
        if h:
            out["help"][c] = h[:3000]
    except Exception as e:  # noqa: BLE001
        out["help"][c] = "help ERR: {}".format(e)

dump_path = "C:/Dev/Sanjuk-Unreal/dumps/maya_probe_convert_import.json"
try:
    os.makedirs(os.path.dirname(dump_path), exist_ok=True)
    with open(dump_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("WROTE " + dump_path)
except Exception as e:  # noqa: BLE001
    print("WRITE_FAILED " + str(e))
