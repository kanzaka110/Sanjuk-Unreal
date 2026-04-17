import unreal

da_path = "/Game/ART/Character/PC/PC_01/OverlaySystem/Poses/Fist_Normal_Guard/PC_01_Fist_Normal_Gaurd_Overlay_DA"
da = unreal.load_asset(da_path)

if da:
    print("=== Class: " + da.get_class().get_name())

    # 전수 스캔 — callable 제외, 값만 출력
    print("\n=== All Attributes ===")
    for attr in sorted(dir(da)):
        if attr.startswith("_"):
            continue
        try:
            val = getattr(da, attr)
            if callable(val):
                continue
            print("  " + attr + " = " + str(val)[:300])
        except:
            pass
else:
    print("DA not found")

print("\n[DONE]")
