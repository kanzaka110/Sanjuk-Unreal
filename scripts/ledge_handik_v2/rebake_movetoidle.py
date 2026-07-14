import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/rebake_movetoidle.json"
BASE = "/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing/"
TARGETS = ["P_Player_Ledge_MoveToIdle_L", "P_Player_Ledge_MoveToIdle_R",
           "P_Player_Ledge_MoveToIdle_Wallless_L", "P_Player_Ledge_MoveToIdle_Wallless_R"]
OVR = {"FlightSpeedThreshold": 10.0}
result = {}
try:
    # PIE 가드
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is not None:
        result["aborted"] = "PIE_RUNNING"
        raise SystemExit

    import importlib, sb_ledge_hand_ik
    importlib.reload(sb_ledge_hand_ik)

    for name in TARGETS:
        path = BASE + name
        sb_ledge_hand_ik.apply(path, overrides=OVR)
        seq = unreal.load_asset(path)
        fps = unreal.AnimationLibrary.get_num_frames(seq) / unreal.AnimationLibrary.get_sequence_length(seq)
        entry = {}
        for c in ("ledge_hand_ik_l", "ledge_hand_ik_r"):
            times, values = unreal.AnimationLibrary.get_float_keys(seq, c)
            entry[c] = [[round(t * fps, 1), round(float(v), 2)] for t, v in zip(times, values)]
        entry["saved"] = bool(unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False))
        result[name] = entry

    # ABP 저장 (지난 턴 PIE로 실패한 것 마무리)
    abp = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
    bp = unreal.load_asset(abp)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    result["abp_saved"] = bool(unreal.EditorAssetLibrary.save_asset(abp, only_if_is_dirty=False))
except SystemExit:
    pass
except Exception:
    import traceback
    result["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(result, fp, indent=1)
print("REBAKE_MTI_DONE")
