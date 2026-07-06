# -*- coding: utf-8 -*-
"""Step1: S_WallHandIKConfig 구조체 + DT_WallHandIK 생성 + Default 행 시딩."""
from mono import bp
import json

DIR = "/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK"

FIELDS = [
    # (name, type, default)
    ("IKStrengthMax",       "float", "1.0"),
    ("AttachStartDist",     "float", "60.0"),
    ("AttachFullDist",      "float", "45.0"),
    ("FrontFullDist",       "float", "10.0"),
    ("AttachDuration",      "float", "0.55"),
    ("ReleaseDuration",     "float", "0.65"),
    ("ReleaseDurationFast", "float", "0.4"),
    ("TurnReleaseDuration", "float", "0.12"),
    ("AttachCurve",         "object:CurveFloat", None),
    ("ReleaseCurve",        "object:CurveFloat", None),
    ("ApproachOffsetDist",  "float", "20.0"),
    ("StandoffR",           "float", "4.0"),
    ("StandoffL",           "float", "2.0"),
    ("FrontHandHalfWidth",  "float", "12.4"),
    ("FrontHandHeight",     "float", "12.4"),
    ("FrontStandoff",       "float", "2.5"),
    ("FwdOffsetJog",        "float", "5.0"),
    ("FwdOffsetRun",        "float", "20.0"),
    ("FwdOffsetSprint",     "float", "60.0"),
    ("HeightOffsetRun",     "float", "-5.0"),
    ("HeightOffsetSprint",  "float", "-10.0"),
    ("TurnBlockHold",       "float", "0.8"),
]

def main():
    fields = []
    for n, t, d in FIELDS:
        f = {"name": n, "type": t}
        if d is not None:
            f["default_value"] = d
        fields.append(f)

    err, out = bp("create_user_defined_struct",
                  save_path=f"{DIR}/S_WallHandIKConfig", fields=fields)
    print("[struct]", "ERR" if err else "OK", out[:500])
    if err:
        return

    err, out = bp("create_data_table",
                  save_path=f"{DIR}/DT_WallHandIK",
                  row_struct=f"{DIR}/S_WallHandIKConfig")
    print("[dt]", "ERR" if err else "OK", out[:500])
    if err:
        return

    values = {n: d for n, t, d in FIELDS if d is not None}
    err, out = bp("add_data_table_row",
                  asset_path=f"{DIR}/DT_WallHandIK",
                  row_name="Default", values=values)
    print("[row]", "ERR" if err else "OK", out[:500])

if __name__ == "__main__":
    main()
