# 전 시퀀스 모디파이어 Apply (2026-07-21) — 각 애님의 '현재 인스턴스 값'을 그대로 실어 재베이크
#
# ⚠ apply_anim_modifier 는 인스턴스 값이 아니라 CDO 기본값으로 적용된다(2026-07-20 실측).
#   → properties 인자로 애님별 값을 매번 명시해야 각자의 안무가 보존된다.
# ⚠ persist=True 는 인스턴스를 '추가'하므로 완료 후 dedupe 필요.
#
# 백업: ledge_curves_backup.json (158종 1330커브) / mod_params_BACKUP_*.json
import json, urllib.request, sys

URL = "http://localhost:9316/mcp"
DIR = "/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing/"
DUMP = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/mod_params_dump.json"
OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/bake_all_current.json"
SKIP_PREFIX = "P_Player_Ledge_End"       # 모디파이어 제거됨


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


anims = json.load(open(DUMP))["anims"]
rep = {"baked": [], "skip": [], "error": {}}
names = [n for n in sorted(anims) if not n.startswith(SKIP_PREFIX)]
only = set(sys.argv[1:])
for i, nm in enumerate(names):
    if only and nm not in only:
        continue
    props = {k: v for k, v in anims[nm].items() if k != "dur"}
    if not props:
        rep["skip"].append(nm)
        continue
    try:
        call("animation_query", "apply_anim_modifier",
             {"asset_path": DIR + nm, "modifier_class": "AM_SBLedgeIK_C",
              "properties": props, "persist": True})
        rep["baked"].append(nm)
    except Exception as e:
        rep["error"][nm] = str(e)[:160]
    if (i + 1) % 25 == 0:
        json.dump(rep, open(OUT, "w"), indent=1, ensure_ascii=False)
        print("  ... %d/%d (err %d)" % (i + 1, len(names), len(rep["error"])), flush=True)

json.dump(rep, open(OUT, "w"), indent=1, ensure_ascii=False)
print("BAKE_ALL_DONE baked=%d skip=%d err=%d" % (len(rep["baked"]), len(rep["skip"]), len(rep["error"])))
for k, v in list(rep["error"].items())[:5]:
    print("   ERR %s : %s" % (k.replace("P_Player_Ledge_", ""), v))
