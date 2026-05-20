"""PC_01_ABP MoveSideProfies (S_MoveSideProfie) default 값 dump.

S_MoveSideProfie 안의 두 array (Default, LockOn_Default) 의
S_MoveSideRange entries (MoveSide enum + Min + Max angle) 확인.

실행:
  UE Editor > Output Log > py "C:/Dev/Sanjuk-Unreal/scripts/dump_moveside_profiles.py"
"""
import unreal

ABP_PATH = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"

abp = unreal.load_asset(ABP_PATH)
if abp is None:
    print("FAILED to load ABP")
else:
    print(f"ABP class: {abp.get_class().get_name()}")
    # AnimBlueprint -> GeneratedClass -> CDO
    gc = None
    try:
        gc = abp.generated_class()
    except Exception as e:
        print(f"generated_class() error: {e}")

    if gc is None:
        try:
            gc = abp.get_editor_property("GeneratedClass")
        except Exception as e:
            print(f"GeneratedClass prop error: {e}")

    if gc is None:
        print("FAILED to get generated class")
    else:
        print(f"GeneratedClass: {gc.get_name()}")
        cdo = unreal.get_default_object(gc) if hasattr(unreal, 'get_default_object') else None
        if cdo is None:
            try:
                cdo = gc.get_default_object()
            except Exception:
                pass
        if cdo is None:
            print("FAILED to get CDO")
        else:
            print(f"CDO: {cdo.get_name()}")
            try:
                profies = cdo.get_editor_property("MoveSideProfies")
                print(f"MoveSideProfies type: {type(profies).__name__}")
                print(f"  export: {profies.export_text() if hasattr(profies, 'export_text') else profies}")

                for prof_name in ("MoveSide_Default", "MoveSide_LockOn_Default"):
                    try:
                        arr = profies.get_editor_property(prof_name)
                        print(f"\n--- {prof_name} (len={len(arr)}) ---")
                        for i, entry in enumerate(arr):
                            try:
                                ms = entry.get_editor_property("MoveSide")
                                mn = entry.get_editor_property("Min")
                                mx = entry.get_editor_property("Max")
                                print(f"  [{i}] MoveSide={ms}  Min={mn}  Max={mx}")
                            except Exception as e:
                                print(f"  [{i}] field err: {e}")
                    except Exception as e:
                        print(f"  {prof_name} err: {e}")
            except Exception as e:
                print(f"MoveSideProfies err: {e}")

            try:
                ht = cdo.get_editor_property("HoldTimeThreshold")
                print(f"\nHoldTimeThreshold: {ht}")
            except Exception as e:
                print(f"HoldTimeThreshold err: {e}")

print("\n=== DONE ===")
