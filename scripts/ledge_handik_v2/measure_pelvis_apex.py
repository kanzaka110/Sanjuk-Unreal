# 애님별 펠비스 수직 정점/최저점 실측 → 스프링 커브 창 산출 근거 (에디터 py 전용)
# 커브 의도: 정점부터 떨어지는 구간에서 스프링 강도가 세진다 (유저 스펙 2026-07-20)
import unreal, json, os, traceback
OUT="C:/Users/SHIFTUP/AppData/Local/Temp/claude/pelvis_apex.json"
DIR="/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing"
try: OPTS=unreal.AnimPoseEvaluationOptions()
except Exception: OPTS=None
data={}
if os.path.exists(OUT):
    try: data=json.load(open(OUT))
    except Exception: data={}
assets=unreal.EditorAssetLibrary.list_assets(DIR, recursive=True, include_folder=False)
if not assets:
    assets=[DIR+"/"+n for n in json.load(open("C:/Users/SHIFTUP/AppData/Local/Temp/claude/derived_windows.json")).keys()]
n=0
for path in assets:
    p=path.split(".")[0]; nm=p.split("/")[-1]
    if nm in data: continue
    try:
        seq=unreal.load_asset(p)
        if not isinstance(seq,unreal.AnimSequence): continue
        dur=float(unreal.AnimationLibrary.get_sequence_length(seq)); nf=int(unreal.AnimationLibrary.get_num_frames(seq))
        step=dur/max(nf,1); zs=[]
        for f in range(nf+1):
            t=min(f*step,dur)
            pose=unreal.AnimPoseExtensions.get_anim_pose_at_time(seq,t,OPTS)
            zs.append((round(t,3), round(float(unreal.AnimPoseExtensions.get_bone_pose(pose,"pelvis",unreal.AnimPoseSpaces.WORLD).translation.z),2)))
        vals=[z for _,z in zs]
        ai=vals.index(max(vals)); apex=zs[ai][0]
        tail=vals[ai:]; bi=ai+tail.index(min(tail)); bottom=zs[bi][0]
        data[nm]={"dur":round(dur,3),"apex":apex,"bottom":bottom,
                  "drop":round(vals[ai]-vals[bi],1),"z_range":round(max(vals)-min(vals),1)}
    except Exception:
        data[nm]={"error":traceback.format_exc()[-150:]}
    n+=1
    if n%10==0: json.dump(data,open(OUT,"w"))
json.dump(data,open(OUT,"w"))
print("APEX_DONE %d"%len(data))
