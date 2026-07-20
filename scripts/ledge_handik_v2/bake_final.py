# 전 시퀀스 최종 베이크 — 손/발 창(실측) + 펠비스 스프링 커브(정점→낙하 구간)
#  스프링 커브 스펙(유저 2026-07-20): 펠비스 수직 정점부터 떨어지는 구간에서 강도가 세진다
#    Start=정점 / Full=정점+0.08 / HoldEnd=최저점(정점+0.45 상한) / End=HoldEnd+0.25
#  낙차 5cm 미만(수직 반동 없는 애님)은 네 값을 모두 dur 로 → 모디파이어 가드가 키를 안 써서 커브 0(스프링 off)
#  ⚠ apply_anim_modifier(persist=True) 는 인스턴스를 '추가' 하므로 완료 후 dedupe 필수
import json, urllib.request, os, sys

URL = "http://localhost:9316/mcp"
DIR = "/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing/"
WIN = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/derived_windows.json"
APEX = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/pelvis_apex.json"
OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/bake_final.json"
MIRROR = {"P_Player_Ledge_Move_ShortR": "P_Player_Ledge_Move_ShortL"}   # 미러 쌍: 값 대칭 강제
FOOT_HOLD = 0.05      # 발 릴리즈 시작 지연 (묶임 시간)
RELEASE_RAMP = 0.15   # 발/손이 부드럽게 떨어지도록
MIN_DROP = 5.0        # 이보다 낙차가 작으면 스프링 off


def call(tool, action, params, timeout=300):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(txt[:180])
    return json.loads(txt)


wins = json.load(open(WIN))
apex = json.load(open(APEX))


def props(nm):
    src = MIRROR.get(nm, nm)            # 미러 쌍은 원본 값을 좌우 스왑해 사용
    mir = src != nm
    w = wins.get(src)
    if not w:
        return None
    p = {}
    for bone, side in (("hand_l", "R" if mir else "L"), ("hand_r", "L" if mir else "R"),
                       ("ball_l", "R" if mir else "L"), ("ball_r", "L" if mir else "R")):
        foot = bone.startswith("ball")
        pre = "FootMove" if foot else "HandMove"
        x = w.get(bone)
        if x:
            p[pre + "Start" + side] = round(x[0] + (FOOT_HOLD if foot else 0.0), 3)
            p[pre + "End" + side] = round(x[1], 3)
        x2 = w.get(bone + "_2")
        p[pre + "2Start" + side] = round(x2[0], 3) if x2 else 0.0
        p[pre + "2End" + side] = round(x2[1], 3) if x2 else 0.0
    p["ReleaseRampTime"] = RELEASE_RAMP
    # 스프링 커브 — 정점→낙하
    a = apex.get(src) or {}
    dur = float(a.get("dur") or w.get("dur") or 1.0)
    if (a.get("drop") or 0) < MIN_DROP:
        for k in ("PelvisSpringStart", "PelvisSpringFull", "PelvisSpringHoldEnd", "PelvisSpringEnd"):
            p[k] = round(dur, 3)                       # 전부 dur = 키 미기록 = 스프링 off
    else:
        ap = float(a["apex"])
        bot = min(float(a["bottom"]), ap + 0.45)
        p["PelvisSpringStart"] = round(ap, 3)
        p["PelvisSpringFull"] = round(min(ap + 0.08, dur), 3)
        p["PelvisSpringHoldEnd"] = round(min(max(bot, ap + 0.1), dur), 3)
        p["PelvisSpringEnd"] = round(min(p["PelvisSpringHoldEnd"] + 0.25, dur), 3)
    return p


rep = {"baked": [], "skip": [], "error": {}}
if os.path.exists(OUT):
    try:
        rep = json.load(open(OUT))
    except Exception:
        pass
done = set(rep["baked"])
only = set(sys.argv[1:])
for nm in sorted(wins.keys()):
    if only and nm not in only:
        continue
    if nm in done:
        continue
    pr = props(nm)
    if not pr:
        rep["skip"].append(nm)
        continue
    try:
        call("animation_query", "apply_anim_modifier",
             {"asset_path": DIR + nm, "modifier_class": "AM_SBLedgeIK_C", "properties": pr, "persist": True})
        rep["baked"].append(nm)
    except RuntimeError as e:
        rep["error"][nm] = str(e)[:120]
    if len(rep["baked"]) % 20 == 0:
        json.dump(rep, open(OUT, "w"), indent=1)
json.dump(rep, open(OUT, "w"), indent=1)
print("FINAL_BAKE_DONE baked=%d skip=%d err=%d" % (len(rep["baked"]), len(rep["skip"]), len(rep["error"])))
