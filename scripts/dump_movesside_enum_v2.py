"""ESBStateMachineMoveSide enum byte<->direction 매핑 dump v2.

v1 의 num_enums() 가 UE 5.7 에서 제거된 듯. UserDefinedEnumLibrary 와
direct property access 로 매핑 재시도.

실행:
  UE Editor > Output Log > py "C:/Dev/Sanjuk-Unreal/scripts/dump_movesside_enum_v2.py"
"""
import unreal

ENUM_PATH = "/Game/Art/Character/DataStruct/ESBStateMachineMoveSide"


def dump_enum_v2() -> None:
    print(f"\n=========== ENUM v2: {ENUM_PATH} ===========")
    e = unreal.load_asset(ENUM_PATH)
    if e is None:
        print("  FAILED to load")
        return

    print(f"  class: {e.get_class().get_name()}")

    # UE 5.7: try get_max_enum_value + iterate
    try:
        max_val = e.get_max_enum_value() if hasattr(e, "get_max_enum_value") else None
        print(f"  get_max_enum_value: {max_val}")
    except Exception as ex:
        print(f"  get_max_enum_value error: {ex}")

    # try Names array (UserDefinedEnum stores _Names property)
    for prop_name in ("Names", "_Names", "DisplayNameMap"):
        try:
            val = e.get_editor_property(prop_name)
            print(f"  prop {prop_name}: {type(val).__name__} -> {val}")
        except Exception as ex:
            print(f"  prop {prop_name} error: {ex}")

    # try UserDefinedEnumLibrary statics
    try:
        for i in range(0, 16):
            try:
                disp = unreal.UserDefinedEnumLibrary.get_display_name_text_by_index(e, i)
                print(f"  index={i}  display='{disp}'")
            except Exception:
                break
    except Exception as ex:
        print(f"  UDEL error: {ex}")

    # try unreal.Enum subclass methods
    for attr in dir(e):
        if any(k in attr.lower() for k in ("enum", "name", "value", "max")) and not attr.startswith("_"):
            try:
                v = getattr(e, attr)
                if callable(v):
                    continue
                print(f"  attr {attr} = {v}")
            except Exception:
                pass

    # Print all bound methods that look enum-related
    print("\n  --- enum-related methods ---")
    for attr in sorted(dir(e)):
        if not attr.startswith("_") and any(k in attr.lower() for k in ("enum", "name", "value", "max", "index")):
            print(f"    .{attr}")


def cross_check_with_pc01_bp() -> None:
    """ABP UpdateMoveSide / Get_MoveSide 의 enum literal 사용 위치 print."""
    print("\n=========== PC_01_ABP enum references ===========")
    abp_path = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
    abp = unreal.load_asset(abp_path)
    if abp is None:
        print("  FAILED to load ABP")
        return
    # AnimBlueprint -> get parent class -> CDO does not work (protected)
    # Try: list referenced asset names (any ChooserTable that references MoveSide enum)
    refs = unreal.EditorAssetLibrary.find_package_referencers_for_asset(ENUM_PATH)
    print(f"  found {len(refs)} referencers of MoveSide enum:")
    for r in refs[:30]:
        print(f"    - {r}")


dump_enum_v2()
cross_check_with_pc01_bp()
print("\n=== DONE v2 ===")