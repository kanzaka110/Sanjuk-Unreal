import unreal

da_path = "/Game/ART/Character/PC/PC_01/OverlaySystem/Poses/Fist_Normal_Guard/PC_01_Fist_Normal_Gaurd_Overlay_DA"
da = unreal.load_asset(da_path)
if da:
    print("=== DA Properties ===")
    for attr in sorted(dir(da)):
        if attr.startswith("_"):
            continue
        try:
            val = da.get_editor_property(attr)
            if val is not None:
                vname = type(val).__name__
                if hasattr(val, 'get_path_name'):
                    print(f"  {attr}: {val.get_path_name()} ({vname})")
                elif hasattr(val, '__len__') and not isinstance(val, str):
                    print(f"  {attr}: [{len(val)} items] ({vname})")
                    for i, item in enumerate(list(val)[:5]):
                        if hasattr(item, 'get_path_name'):
                            print(f"    [{i}]: {item.get_path_name()}")
                        else:
                            print(f"    [{i}]: {item}")
                else:
                    print(f"  {attr}: {val} ({vname})")
        except:
            pass
else:
    print("DA not found")

print("\n[DONE]")
