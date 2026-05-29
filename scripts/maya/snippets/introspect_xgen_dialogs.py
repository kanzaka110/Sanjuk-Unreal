# -*- coding: utf-8 -*-
"""XGen UI 다이얼로그 모듈의 __file__ 경로 + 전체 함수 enumerate.

Convert/Export Cache/Import/CurveToGuide 다이얼로그가 실제로 부르는 워커 함수를 찾기 위해
소스 파일 경로를 잡는다 (그 다음 Read 로 직접 읽음). read-only.
"""
import json
import os
import sys
import inspect

out = {"modules": {}, "errors": []}

TARGETS = (
    "xgenm.ui.dialogs.xgIgConvertToInteractiveGroomUI",
    "xgenm.ui.dialogs.igExport",
    "xgenm.ui.dialogs.igImport",
    "xgenm.ui.dialogs.xgIgCurveToGuideUI",
    "xgenm.ui.dialogs.xgIgCreateInteractiveDescription",
    "xgenm.xmaya.xgmExternalAPI",
)

for mod_name in TARGETS:
    info = {"file": None, "functions": []}
    try:
        mod = sys.modules.get(mod_name)
        if mod is None:
            mod = __import__(mod_name, fromlist=["*"])
        info["file"] = getattr(mod, "__file__", None)
        for name, obj in inspect.getmembers(mod):
            if name.startswith("_"):
                continue
            if inspect.isfunction(obj) or inspect.isbuiltin(obj):
                try:
                    sig = str(inspect.signature(obj))
                except Exception:  # noqa: BLE001
                    sig = "(?)"
                info["functions"].append("{}{}".format(name, sig))
    except Exception as e:  # noqa: BLE001
        out["errors"].append("{}: {}".format(mod_name, e))
    out["modules"][mod_name] = info

dump_path = "C:/Dev/Sanjuk-Unreal/dumps/maya_introspect_dialogs.json"
try:
    os.makedirs(os.path.dirname(dump_path), exist_ok=True)
    with open(dump_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("WROTE " + dump_path)
except Exception as e:  # noqa: BLE001
    print("WRITE_FAILED " + str(e))
