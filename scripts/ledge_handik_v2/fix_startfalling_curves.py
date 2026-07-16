# Start_Falling 2종: 손 이동창 커브 제거 -> ik 상수1 (그랩 애님 = Idle급 처리)
import unreal, json
BASE="/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing/"
ANIMS=["P_Player_Ledge_Start_Falling","P_Player_Ledge_Start_Falling_Wallless"]
out={}; pkgs=[]
for a in ANIMS:
    seq=unreal.load_asset(BASE+a); e={}
    try:
        for c in ("ledge_hand_ik_l","ledge_hand_ik_r","ledge_hand_move_l","ledge_hand_move_r"):
            if unreal.AnimationLibrary.does_curve_exist(seq,c,unreal.RawCurveTrackTypes.RCT_FLOAT):
                unreal.AnimationLibrary.remove_curve(seq,c)
        for c in ("ledge_hand_ik_l","ledge_hand_ik_r"):
            unreal.AnimationLibrary.add_curve(seq,c)
            unreal.AnimationLibrary.add_float_curve_key(seq,c,0.0,1.0)
        # 결과 리포트
        for c in ("ledge_hand_ik_l","ledge_hand_ik_r","ledge_hand_move_l","ledge_hand_move_r"):
            if unreal.AnimationLibrary.does_curve_exist(seq,c,unreal.RawCurveTrackTypes.RCT_FLOAT):
                r=unreal.AnimationLibrary.get_float_keys(seq,c)
                e[c]=[[round(float(t),3),round(float(v),2)] for t,v in zip(r[0],r[1])]
            else:
                e[c]="제거됨"
        try: unreal.EditorAssetLibrary.checkout_asset(BASE+a)
        except Exception: pass
        pkgs.append(seq.get_outermost())
    except Exception:
        import traceback; e["error"]=traceback.format_exc()[-300:]
    out[a]=e
if pkgs:
    out["_saved"]=bool(unreal.EditorLoadingAndSavingUtils.save_packages(pkgs,only_dirty=False))
with open("C:/Users/SHIFTUP/AppData/Local/Temp/claude/fix_sf.json","w") as f:
    json.dump(out,f,indent=1)
print("FIX_SF_DONE")
