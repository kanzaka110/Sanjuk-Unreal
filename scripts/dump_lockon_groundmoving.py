"""
N_LockOn_GroundMoving sub-chooser 구조 덤프.
Circle Strafe Row를 올바른 위치(지속 loop용)에 추가하기 위한 기반 자료.

UE 에디터 Python 콘솔에서:
  exec(open(r'C:/Dev/Sanjuk-Unreal/scripts/dump_lockon_groundmoving.py').read())
"""
import unreal

ROOT = "/Game/Art/Character/PC/PC_01/StateMachine/GroundMoving.GroundMoving:N_LockOn_GroundMoving"

ct = unreal.load_object(None, ROOT)
if ct is None:
    print(f"FAILED to load {ROOT}")
else:
    print(f"=== {ROOT} ===")
    try:
        columns = ct.get_editor_property("ColumnsStructs")
        print(f"Columns: {len(columns)}")
        for ci, col in enumerate(columns):
            try:
                ss = col.get_struct() if hasattr(col, "get_struct") else None
                tn = ss.get_name() if ss else type(col).__name__
            except Exception:
                tn = "UnknownStruct"
            print(f"\n--- col[{ci}] type={tn} ---")
            try:
                txt = col.export_text() if hasattr(col, "export_text") else repr(col)
                lines = txt.splitlines()
                for line in lines[:30]:
                    print(f"    {line}")
                if len(lines) > 30:
                    print(f"    ... (+{len(lines)-30} lines)")
            except Exception as e:
                print(f"    export_text error: {e}")
    except Exception as e:
        print(f"ColumnsStructs error: {e}")

    try:
        disabled = ct.get_editor_property("DisabledRows")
        print(f"\nDisabledRows: {list(disabled)}")
    except Exception as e:
        print(f"DisabledRows error: {e}")

print("\n=== DONE ===")
