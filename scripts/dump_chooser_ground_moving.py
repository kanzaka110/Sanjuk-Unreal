"""
UE 에디터 Python 콘솔에서 실행.
/Game/Art/Character/PC/PC_01/StateMachine/GroundMoving ChooserTable의
N_LockOn_Transit_Sprinting / Walking / Jogging / Running 4개 sub-chooser의
ResultsStructs 와 ColumnsStructs 를 dump 해서 Sprint_to_Battle_Jog_* 4종 위치 특정.

Run:
  1. UE 에디터에서 [Output Log] 또는 [Window > Developer Tools > Python Console] 열기
  2. `py "C:/Dev/Sanjuk-Unreal/scripts/dump_chooser_ground_moving.py"` 실행
  3. 결과를 사용자가 복사해서 공유
"""
import unreal

ROOT = "/Game/Art/Character/PC/PC_01/StateMachine/GroundMoving.GroundMoving"
SUB_CHOOSER_SUFFIXES = [
    "",  # root
    ":N_LockOn_TransitToGroundMoving",
    ":N_LockOn_TransitToGroundMoving.N_LockOn_Transit_Walking",
    ":N_LockOn_TransitToGroundMoving.N_LockOn_Transit_Jogging",
    ":N_LockOn_TransitToGroundMoving.N_LockOn_Transit_Running",
    ":N_LockOn_TransitToGroundMoving.N_LockOn_Transit_Sprinting",
    ":N_LockOn_GroundMoving",
    ":N_TransitToGroundMoving_Peaceful",
    ":N_TransitToGroundMoving_Battle",
]

def ipath(suf):
    return ROOT + suf


def struct_to_dict(s):
    """FInstancedStruct -> dict via reflection. Returns (type_name, fields)."""
    try:
        # InstancedStruct has get_struct() returning the concrete UScriptStruct
        ss = s.get_struct() if hasattr(s, "get_struct") else None
        type_name = ss.get_name() if ss else type(s).__name__
    except Exception:
        type_name = "UnknownInstancedStruct"
    fields = {}
    try:
        # Enumerate properties via export_text (most reliable for unknown struct types)
        txt = s.export_text() if hasattr(s, "export_text") else repr(s)
        fields["__export__"] = txt
    except Exception as e:
        fields["__export_error__"] = str(e)
    return type_name, fields


def dump_chooser(obj_path):
    print(f"\n=========== {obj_path} ===========")
    ct = unreal.load_object(None, obj_path)
    if ct is None:
        print("  FAILED to load")
        return
    try:
        results = ct.get_editor_property("ResultsStructs")
    except Exception as e:
        print(f"  get ResultsStructs error: {e}")
        results = []
    try:
        columns = ct.get_editor_property("ColumnsStructs")
    except Exception as e:
        print(f"  get ColumnsStructs error: {e}")
        columns = []
    try:
        disabled = ct.get_editor_property("DisabledRows")
    except Exception:
        disabled = []

    print(f"  rows={len(results)} cols={len(columns)} disabled={list(disabled)}")

    # Columns
    print("  --- Columns ---")
    for ci, col in enumerate(columns):
        t, f = struct_to_dict(col)
        print(f"  col[{ci}] type={t}")
        exp = f.get("__export__", "")
        # 줄바꿈 많으면 일부만
        lines = exp.splitlines()
        for line in lines[:40]:
            print(f"      {line}")
        if len(lines) > 40:
            print(f"      ... (+{len(lines)-40} lines)")

    # Results
    print("  --- Results ---")
    for ri, res in enumerate(results):
        t, f = struct_to_dict(res)
        exp = f.get("__export__", "")
        first = exp.splitlines()[0] if exp else ""
        print(f"  row[{ri}] type={t}  {first[:200]}")


for suf in SUB_CHOOSER_SUFFIXES:
    try:
        dump_chooser(ipath(suf))
    except Exception as e:
        print(f"[ERROR] {suf}: {e}")

print("\n=== DONE ===")
