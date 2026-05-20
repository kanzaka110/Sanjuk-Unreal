"""GroundIdle Chooser nested sub-chooser 전수 dump.

P_Player_Fist_Battle_Jog_Stop_* 4 row 가 어떤 column 의 어떤 MoveSide enum 값과
매핑되는지 확정. dump_chooser_ground_moving.py 와 동일 패턴 (export_text 기반).

전제:
  - UE Editor 실행 중
  - SB2 의 경우 PythonScriptPlugin 활성 (.uproject Plugins 배열 또는 Plugin Manager UI)
    — feedback_sb2_python_plugin_disabled.md 가 monolith/runreal 경로만 막혀있고,
      Editor Output Log > Cmd dropdown=Python 콘솔은 별개일 수 있음

실행:
  1. UE 에디터에서 [Window > Developer Tools > Output Log] 열기
  2. Cmd 드롭다운을 'Python' 으로
  3. 다음 입력: py "C:/Dev/Sanjuk-Unreal/scripts/dump_chooser_ground_idle.py"
  4. 출력 전체 복사 → 채팅에 붙여넣기
"""
import unreal

ROOT = "/Game/Art/Character/PC/PC_01/StateMachine/GroundIdle.GroundIdle"
SUB_CHOOSER_SUFFIXES = [
    "",
    ":N_Battle_TransitToGroundIdle",
    ":N_Battle_GroundIdle",
    ":N_Peaceful_TransitToGroundIdle",
    ":N_Peaceful_GroundIdle",
    ":N_LockOn_TransitToGroundIdle",
    ":N_LockOn_GroundIdle",
    ":N_Battle_TurnInPlace",
    ":N_Peaceful_TurnInPlace",
]


def ipath(suf):
    return ROOT + suf


def struct_to_dict(s):
    try:
        ss = s.get_struct() if hasattr(s, "get_struct") else None
        type_name = ss.get_name() if ss else type(s).__name__
    except Exception:
        type_name = "UnknownInstancedStruct"
    fields = {}
    try:
        txt = s.export_text() if hasattr(s, "export_text") else repr(s)
        fields["__export__"] = txt
    except Exception as e:
        fields["__export_error__"] = str(e)
    return type_name, fields


def dump_chooser(obj_path):
    print(f"\n=========== {obj_path} ===========")
    ct = unreal.load_object(None, obj_path)
    if ct is None:
        print("  FAILED to load (sub-object name may not exist)")
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

    print("  --- Columns ---")
    for ci, col in enumerate(columns):
        t, f = struct_to_dict(col)
        print(f"  col[{ci}] type={t}")
        exp = f.get("__export__", "")
        lines = exp.splitlines()
        for line in lines[:60]:
            print(f"      {line}")
        if len(lines) > 60:
            print(f"      ... (+{len(lines) - 60} lines)")

    print("  --- Results ---")
    for ri, res in enumerate(results):
        t, f = struct_to_dict(res)
        exp = f.get("__export__", "")
        lines = exp.splitlines()
        first = lines[0] if lines else ""
        print(f"  row[{ri}] type={t}  {first[:240]}")
        if len(lines) > 1:
            for ln in lines[1:6]:
                print(f"          {ln[:240]}")


for suf in SUB_CHOOSER_SUFFIXES:
    try:
        dump_chooser(ipath(suf))
    except Exception as e:
        print(f"[ERROR] {suf}: {e}")

print("\n=== DONE ===")
