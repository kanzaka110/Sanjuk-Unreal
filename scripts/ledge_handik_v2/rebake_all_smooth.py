import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/rebake_all_smooth.json"
DIR = "/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing"
MOD = "/Game/Art/TA/AnimModifiers/AM_SBLedgeHandIK"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
SLOW_REGRIP = {"P_Player_Ledge_MoveToIdle_L", "P_Player_Ledge_MoveToIdle_R",
               "P_Player_Ledge_MoveToIdle_Wallless_L", "P_Player_Ledge_MoveToIdle_Wallless_R"}
result = {"applied": 0, "failed": [], "save_failed": []}
try:
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if w is not None:
        result["aborted"] = "PIE_RUNNING"
        raise SystemExit

    # 1) ABP 저장 (스트레치 밸브 — 컴파일 済, 저장 대기분)
    bp = unreal.load_asset(ABP)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    result["abp_saved"] = bool(unreal.EditorAssetLibrary.save_asset(ABP, only_if_is_dirty=False))

    # 2) 모디파이어 BP 램프 디폴트 갱신 (CDO)
    try:
        mod_cls = unreal.load_object(None, MOD + ".AM_SBLedgeHandIK_C")
        cdo = unreal.get_default_object(mod_cls)
        cdo.set_editor_property("PlantRampFrames", 3)
        cdo.set_editor_property("ReleaseRampFrames", 2)
        result["mod_defaults"] = "ok"
        unreal.EditorAssetLibrary.save_asset(MOD, only_if_is_dirty=False)
    except Exception as e:
        result["mod_defaults"] = repr(e)[:120]

    # 3) 전체 스무스 리베이크
    import importlib, sb_ledge_hand_ik
    importlib.reload(sb_ledge_hand_ik)
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    assets = ar.get_assets_by_path(DIR, recursive=True)
    seq_paths = sorted(str(a.package_name) for a in assets
                       if str(a.asset_class_path.asset_name) == "AnimSequence")
    result["total"] = len(seq_paths)
    for path in seq_paths:
        name = path.split("/")[-1]
        try:
            ovr = {"FlightSpeedThreshold": 10.0} if name in SLOW_REGRIP else None
            sb_ledge_hand_ik.apply(path, overrides=ovr)
            result["applied"] += 1
        except Exception as e:
            result["failed"].append(name + " : " + repr(e)[:80])
    for path in seq_paths:
        try:
            if not unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=True):
                result["save_failed"].append(path.split("/")[-1])
        except Exception as e:
            result["save_failed"].append(path.split("/")[-1] + " : " + repr(e)[:80])

    # 검증 샘플: 파일럿 키 확인
    seq = unreal.load_asset(DIR + "/P_Player_Ledge_Move_ShortL_Wallless")
    fps = unreal.AnimationLibrary.get_num_frames(seq) / unreal.AnimationLibrary.get_sequence_length(seq)
    times, values = unreal.AnimationLibrary.get_float_keys(seq, "ledge_hand_ik_l")
    result["pilot_L_keys"] = [[round(t * fps, 1), round(float(v), 3)] for t, v in zip(times, values)]
except SystemExit:
    pass
except Exception:
    import traceback
    result["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(result, fp, indent=1)
print("REBAKE_SMOOTH_DONE")
