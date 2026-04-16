import unreal

idle_path = "/Game/ART/Character/PC/PC_01/OverlaySystem/Poses/Fist_Normal_Guard/PC_01_Fist_Normal_Guard_Pose_Idle"
move_path = "/Game/ART/Character/PC/PC_01/OverlaySystem/Poses/Fist_Normal_Guard/PC_01_Fist_Normal_Guard_Pose_Move"

for label, path in [("IDLE", idle_path), ("MOVE", move_path)]:
    seq = unreal.load_asset(path)
    if seq:
        print("\n=== " + label + " ===")
        try:
            print("  AdditiveAnimType: " + str(seq.get_editor_property("additive_anim_type")))
        except Exception as e:
            print("  AdditiveAnimType err: " + str(e)[:80])
        try:
            print("  RefPoseType: " + str(seq.get_editor_property("ref_pose_type")))
        except Exception as e:
            print("  RefPoseType err: " + str(e)[:80])
        try:
            ref = seq.get_editor_property("ref_pose_seq")
            print("  RefPoseSeq: " + (ref.get_path_name() if ref else "None"))
        except Exception as e:
            print("  RefPoseSeq err: " + str(e)[:80])
        try:
            print("  RefFrameIndex: " + str(seq.get_editor_property("ref_frame_index")))
        except Exception as e:
            print("  RefFrameIndex err: " + str(e)[:80])
    else:
        print(label + ": NOT FOUND")

print("\n[DONE]")
