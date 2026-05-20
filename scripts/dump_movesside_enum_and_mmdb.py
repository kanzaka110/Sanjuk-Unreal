"""ESBStateMachineMoveSide enum 현재 정의 + PC_01 MotionMatching Database dump.

Chooser MoveSide column 의 Value(byte) 와 ValueName(NewEnumeratorN) 어긋남
검증용. Enum 재정렬 흔적이면 ABP MoveSide 변수가 실제 어떤 byte 를
send 하는지 결정함.

실행:
  UE Editor > Output Log > Cmd=Python:
  py "C:/Dev/Sanjuk-Unreal/scripts/dump_movesside_enum_and_mmdb.py"
"""
import unreal

ENUM_PATH = "/Game/Art/Character/DataStruct/ESBStateMachineMoveSide"
ABP_PATH = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
PC01_ROOT = "/Game/Art/Character/PC/PC_01"


def dump_enum():
    print(f"\n=========== ENUM: {ENUM_PATH} ===========")
    e = unreal.load_asset(ENUM_PATH)
    if e is None:
        print("  FAILED to load enum")
        return
    print(f"  class: {e.get_class().get_name()}")
    try:
        n = e.num_enums()
        print(f"  num_enums: {n}")
        for i in range(n):
            try:
                value = e.get_value_by_index(i)
            except Exception as ex:
                value = f"err({ex})"
            try:
                name = e.get_name_by_index(i)
            except Exception as ex:
                name = f"err({ex})"
            try:
                disp = unreal.UserDefinedEnumLibrary.get_display_name_text_by_index(e, i)
            except Exception as ex:
                disp = f"err({ex})"
            print(f"  [{i}] value={value}  name={name}  display={disp}")
    except Exception as ex:
        print(f"  enum dump error: {ex}")
    try:
        print("  export_text head:")
        txt = e.export_text() if hasattr(e, "export_text") else ""
        for line in txt.splitlines()[:30]:
            print(f"    {line}")
    except Exception:
        pass


def dump_pose_search_dbs():
    print(f"\n=========== PoseSearchDatabase under {PC01_ROOT} ===========")
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    if ar is None:
        print("  AssetRegistry unavailable")
        return
    filt = unreal.ARFilter(
        package_paths=[PC01_ROOT],
        recursive_paths=True,
        class_names=["PoseSearchDatabase"],
    )
    try:
        assets = ar.get_assets(filt)
    except Exception as ex:
        print(f"  ARFilter error: {ex}")
        assets = []
    if not assets:
        print("  no PoseSearchDatabase under PC_01")
    for ad in assets:
        try:
            path = str(ad.get_asset().get_path_name())
        except Exception:
            path = str(ad.object_path)
        print(f"  - {path}")
        try:
            db = ad.get_asset()
            if db:
                for prop_name in ["Schema", "Tags", "ExcludeFromDatabaseTags"]:
                    try:
                        v = db.get_editor_property(prop_name)
                        s = str(v)[:300] if v is not None else None
                        print(f"      {prop_name}={s}")
                    except Exception:
                        pass
        except Exception:
            pass


def dump_stop_sequences():
    print(f"\n=========== AnimSequences matching P_Player_Fist_Battle_Jog_Stop ===========")
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    if ar is None:
        return
    filt = unreal.ARFilter(
        package_paths=[PC01_ROOT, "/Game/Art/Animation"],
        recursive_paths=True,
        class_names=["AnimSequence"],
    )
    try:
        assets = ar.get_assets(filt)
    except Exception as ex:
        print(f"  ARFilter error: {ex}")
        return
    matched = []
    for ad in assets:
        try:
            name = str(ad.asset_name)
        except Exception:
            continue
        if "P_Player_Fist_Battle_Jog_Stop" in name or "Battle_Jog_Stop" in name:
            try:
                path = str(ad.package_name) + "." + name
            except Exception:
                path = name
            matched.append(path)
    print(f"  found {len(matched)} matching sequences")
    for p in matched[:20]:
        print(f"  - {p}")


def dump_abp_movesside_var():
    print(f"\n=========== ABP MoveSide variable in {ABP_PATH} ===========")
    bp = unreal.load_asset(ABP_PATH)
    if bp is None:
        print("  FAILED to load ABP")
        return
    cdo = None
    try:
        gen_class = bp.get_editor_property("GeneratedClass")
        if gen_class:
            cdo = unreal.get_default_object(gen_class)
    except Exception as ex:
        print(f"  GeneratedClass error: {ex}")
    if cdo is None:
        print("  no CDO")
        return
    for vname in ["MoveSide", "moveSide", "Move_Side", "PendingMoveSide"]:
        try:
            v = cdo.get_editor_property(vname)
            print(f"  {vname} = {v} (type {type(v).__name__})")
        except Exception:
            pass


dump_enum()
dump_pose_search_dbs()
dump_stop_sequences()
dump_abp_movesside_var()
print("\n=== DONE ===")
