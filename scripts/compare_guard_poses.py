import unreal

idle_path = "/Game/ART/Character/PC/PC_01/OverlaySystem/Poses/Fist_Normal_Guard/PC_01_Fist_Normal_Guard_Pose_Idle"
move_path = "/Game/ART/Character/PC/PC_01/OverlaySystem/Poses/Fist_Normal_Guard/PC_01_Fist_Normal_Guard_Pose_Move"

idle = unreal.load_asset(idle_path)
move = unreal.load_asset(move_path)

if not idle or not move:
    print("ERROR: asset not found")
else:
    print("=== Idle info ===")
    print("  frames: " + str(idle.get_editor_property("number_of_sampled_frames")))
    print("  duration: " + str(idle.get_editor_property("sequence_length")))

    print("\n=== Move info ===")
    print("  frames: " + str(move.get_editor_property("number_of_sampled_frames")))
    print("  duration: " + str(move.get_editor_property("sequence_length")))

    # 커브 값 비교
    print("\n=== Curve value comparison ===")
    curves_to_check = [
        "layering_spine", "layering_spine_add",
        "layering_head", "layering_head_add",
        "layering_arm_l", "layering_arm_l_add", "layering_arm_l_ls",
        "layering_arm_r", "layering_arm_r_add", "layering_arm_r_ls",
        "layering_hand_l", "layering_hand_r",
        "layering_legs", "layering_pelvis",
        "enable_spinerotation", "enable_handik_l", "enable_handik_r",
    ]
    for c in curves_to_check:
        idle_val = "N/A"
        move_val = "N/A"
        try:
            idle_val = str(round(idle.evaluate_curve_data(c, 0.0), 3))
        except:
            pass
        try:
            move_val = str(round(move.evaluate_curve_data(c, 0.0), 3))
        except:
            pass
        match = "OK" if idle_val == move_val else "DIFF"
        print("  " + c + ": Idle=" + idle_val + " Move=" + move_val + " " + match)

print("\n[DONE]")
