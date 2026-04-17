import unreal

da_path = "/Game/ART/Character/PC/PC_01/OverlaySystem/Poses/Fist_Normal_Guard/PC_01_Fist_Normal_Gaurd_Overlay_DA"
da = unreal.load_asset(da_path)

if da:
    print("=== Class: " + da.get_class().get_name())
    print("=== Parent: " + da.get_class().get_super_class().get_name())

    # 방법1: CDO 프로퍼티 전수 스캔
    print("\n=== All Properties (dir scan) ===")
    for attr in sorted(dir(da)):
        if attr.startswith("_") or attr.startswith("set_") or attr.startswith("call_"):
            continue
        if attr in ("get_class", "get_editor_property", "get_name", "get_outer",
                     "get_path_name", "get_full_name", "get_world", "get_fname",
                     "get_default_object", "get_type_name", "get_outermost"):
            continue
        try:
            val = getattr(da, attr)
            if callable(val):
                continue
            print("  " + attr + " = " + str(val)[:200])
        except:
            pass

    # 방법2: UE property iterator
    print("\n=== Editor Properties (brute force) ===")
    test_names = [
        "idle_pose", "move_pose", "idle_animation", "move_animation",
        "overlay_pose_idle", "overlay_pose_move", "overlay_abp",
        "pose_idle", "pose_move", "blend_time", "blend_in", "blend_out",
        "animation_idle", "animation_move", "anim_idle", "anim_move",
        "overlay_animation", "data", "poses", "animations",
        "IdlePose", "MovePose", "OverlayABP", "BlendTime",
        "AnimationData", "PoseData", "OverlayPoses",
    ]
    for name in test_names:
        try:
            val = da.get_editor_property(name)
            if val is not None:
                print("  FOUND: " + name + " = " + str(val)[:200])
        except:
            pass

    # 방법3: export text
    print("\n=== Export Properties ===")
    try:
        props = unreal.EditorAssetLibrary.get_metadata_tag_values(da_path)
        if props:
            for k, v in props.items():
                print("  " + str(k) + " = " + str(v)[:200])
    except Exception as e:
        print("  metadata err: " + str(e)[:80])

    # 방법4: PDA 블루프린트 클래스의 변수 확인
    print("\n=== PDA_OverlayData Blueprint Variables ===")
    pda_bp_path = "/Game/ART/Character/PC/PC_01/OverlaySystem/Data/PDA_OverlayData"
    pda_bp = unreal.load_asset(pda_bp_path)
    if pda_bp:
        print("  PDA BP class: " + pda_bp.get_class().get_name())
        gen = pda_bp.get_editor_property("generated_class") if hasattr(pda_bp, "get_editor_property") else None
        if gen:
            print("  Generated class: " + gen.get_name())
    else:
        print("  PDA_OverlayData not found at " + pda_bp_path)
else:
    print("DA not found")

print("\n[DONE]")
