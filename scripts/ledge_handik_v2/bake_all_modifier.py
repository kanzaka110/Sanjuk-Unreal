# derived_windows.json 값으로 AM_SBLedgeIK 를 애님별 적용(커브 재베이크) — 로컬 python
# ⚠ apply_anim_modifier 는 인스턴스 값이 아니라 **CDO 기본값**으로 적용된다 (2026-07-20 실측).
#   → properties 로 애님별 값을 매번 명시해야 한다. persist=true 로 스택에도 반영.
# 이탈/정지 계열, 창 없는 애님, PRESERVE 2종은 제외.
import json, urllib.request, sys

URL = "http://localhost:9316/mcp"
WIN = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/derived_windows.json"
OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/bake_report.json"
DIR = "/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing/"
CLS = "AM_SBLedgeIK_C"
# 2026-07-20: 유저 지시로 전량 적용 — 제외 없음
#   1차 창은 그래프에 이미 가드(End>Start)가 있어 창 0/0 이면 블록 스킵 → 키 중복/크래시 없음 (실측 확인)
PRESERVE = set()
SKIP = ()


def call(tool, action, params, timeout=300):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(txt[:200])
    return json.loads(txt)


def props(w):
    dur = w["dur"]
    p = {}
    for bone, pre in (("hand_l", "HandMove"), ("hand_r", "HandMove"), ("ball_l", "FootMove"), ("ball_r", "FootMove")):
        side = "L" if bone.endswith("_l") else "R"
        w1, w2 = w.get(bone), w.get(bone + "_2")
        p[pre + "Start" + side] = round(w1[0], 3) if w1 else 0.0
        p[pre + "End" + side] = round(min(w1[1], dur), 3) if w1 else 0.0
        p[pre + "2Start" + side] = round(w2[0], 3) if w2 else 0.0
        p[pre + "2End" + side] = round(min(w2[1], dur), 3) if w2 else 0.0
    p["bAutoDetect"] = False   # 워크플로 A: 인스턴스 값이 정본 — 적용 시 자동검출 끄고 패널 값 사용
    ends = [w[b][1] for b in ("hand_l", "hand_r") if w.get(b)]
    if ends:
        base = max(ends)
        for k, d in (("PelvisSpringStart", 0.05), ("PelvisSpringFull", 0.20),
                     ("PelvisSpringHoldEnd", 0.55), ("PelvisSpringEnd", 0.90)):
            p[k] = round(min(base + d, dur), 3)
    return p


wins = json.load(open(WIN))
only = set(sys.argv[1:])
import os
rep = {"baked": [], "skip": [], "error": {}}
if os.path.exists(OUT):          # 재개 — 이미 베이크한 것 건너뜀
    try:
        rep = json.load(open(OUT))
    except Exception:
        pass
done = set(rep["baked"])
for nm, w in sorted(wins.items()):
    if only and nm not in only:
        continue
    if nm in done:
        continue
    if False:
        rep["skip"].append(nm)
        continue
    try:
        call("animation_query", "apply_anim_modifier",
             {"asset_path": DIR + nm, "modifier_class": CLS, "properties": props(w), "persist": True})
        rep["baked"].append(nm)
    except RuntimeError as e:
        rep["error"][nm] = str(e)[:150]
    if len(rep["baked"]) % 20 == 0:
        json.dump(rep, open(OUT, "w"), indent=1)
json.dump(rep, open(OUT, "w"), indent=1)
print("BAKE_DONE baked=%d skip=%d err=%d" % (len(rep["baked"]), len(rep["skip"]), len(rep["error"])))
