# -*- coding: utf-8 -*-
"""XGen Interactive Groom API ground-truth introspection v2.

read-only. 실제 존재하는 xgm* 명령 + 플래그 + xgenm python API 의 convert/cache 함수를
잡아 추측 코드를 교체할 근거를 만든다. dumps/maya_introspect_xgen_api.json 에 write.
"""
import json
import os

import maya.cmds as cmds
import maya.mel as mel

out = {
    "command_exists": {},
    "command_help": {},
    "xgenm_modules": [],
    "xgenm_convert_cache_callables": [],
    "errors": [],
}

CANDIDATES = (
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
    "xgmSplineQuery",
    "xgmSetArchiveBBox",
    "AbcExport",
    "AbcImport",
)

# 1. mel whatIs — 명령 존재 + 출처(command/MEL proc/Python)
for c in CANDIDATES:
    try:
        out["command_exists"][c] = mel.eval('whatIs "{}"'.format(c))
    except Exception as e:  # noqa: BLE001
        out["command_exists"][c] = "ERR: {}".format(e)

# 2. cmds.help — 실제 command 라면 플래그 시그니처 덤프
for c in CANDIDATES:
    try:
        h = cmds.help(c)
        if h:
            out["command_help"][c] = h[:4000]
    except Exception:  # noqa: BLE001
        pass

# 3. 로드된 xgenm python 모듈 enumerate + convert/cache/interactive 키워드 callable
try:
    import sys
    import inspect as _inspect

    KW = ("convert", "interactive", "cache", "guide", "curve", "groom", "spline")
    for mod_name in sorted(list(sys.modules.keys())):
        if "xgen" not in mod_name.lower():
            continue
        out["xgenm_modules"].append(mod_name)
        mod = sys.modules.get(mod_name)
        if mod is None:
            continue
        try:
            members = _inspect.getmembers(mod)
        except Exception:  # noqa: BLE001
            continue
        for name, obj in members:
            if name.startswith("_"):
                continue
            low = name.lower()
            if not any(k in low for k in KW):
                continue
            if _inspect.isfunction(obj) or _inspect.isbuiltin(obj) or _inspect.ismethod(obj):
                try:
                    sig = str(_inspect.signature(obj))
                except Exception:  # noqa: BLE001
                    sig = "(?)"
                out["xgenm_convert_cache_callables"].append(
                    "{}.{}{}".format(mod_name, name, sig)
                )
except Exception as e:  # noqa: BLE001
    out["errors"].append("xgenm scan: {}".format(e))

# dedup
out["xgenm_convert_cache_callables"] = sorted(set(out["xgenm_convert_cache_callables"]))

dump_path = "C:/Dev/Sanjuk-Unreal/dumps/maya_introspect_xgen_api.json"
try:
    os.makedirs(os.path.dirname(dump_path), exist_ok=True)
    with open(dump_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("WROTE " + dump_path)
except Exception as e:  # noqa: BLE001
    print("WRITE_FAILED " + str(e))
