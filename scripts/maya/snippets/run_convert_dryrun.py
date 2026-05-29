# -*- coding: utf-8 -*-
"""groom_convert_xgen(dry_run=True) 를 라이브 Evie 씬에 대해 plan 생성. 씬 변경 없음."""
import json
import os
import sys

sys.path.insert(0, "C:/Dev/MayaMCP/src")
for _m in list(sys.modules):
    if "groom_convert_xgen" in _m:
        del sys.modules[_m]

from mayatools.thirdparty.groom_convert_xgen import groom_convert_xgen

res = groom_convert_xgen(dry_run=True)

dump_path = "C:/Dev/Sanjuk-Unreal/dumps/groom_convert_dryrun.json"
os.makedirs(os.path.dirname(dump_path), exist_ok=True)
with open(dump_path, "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=2)
print("WROTE " + dump_path)
