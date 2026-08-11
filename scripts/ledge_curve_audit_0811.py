# -*- coding: utf-8 -*-
"""LedgeClimbing 시퀀스 커브/모디파이어 전수 감사 — 읽기 전용 (2026-08-11)

목적: 재베이크 전에 현재 상태를 확정한다.
  1) 모디파이어 스택 중복 여부 (중복 시 마지막 것만 반영 = 값이 뒤집히는 알려진 함정)
  2) 인스턴스 파라미터 값 (apply_anim_modifier 는 CDO 값을 쓰므로 properties 없이 구우면 인스턴스값 소실)
  3) 현재 커브 키 전량 = 재베이크 롤백용 스냅샷

⚠ 이 스크립트는 아무것도 쓰지 않는다. 굽는 건 결과 확인 후 별도.
"""
import json
import urllib.request

MCP = "http://localhost:9316/mcp"
DIR = "/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing"
CURVES = ("ledge_hand_ik_l", "ledge_hand_ik_r", "ledge_hand_move_l", "ledge_hand_move_r",
          "ledge_foot_ik_l", "ledge_foot_ik_r", "ledge_foot_move_l", "ledge_foot_move_r",
          "ledge_pelvis_spring", "ledgephysanimalpha")
OUT = (r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\H---------Claude-Sanjuk-Unreal"
       r"\13217e5f-1fe8-48a4-a44a-f44cb2b73afa\scratchpad\ledge_curve_audit_0811.json")


def call(tool, action, params, timeout=300):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(MCP, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        return {"_ERR": txt[:300]}
    try:
        return json.loads(txt)
    except Exception:
        return {"_RAW": txt[:300]}


def anim(a, p):
    return call("animation_query", a, p)


assets = call("editor_query", "list_assets", {"directory": DIR, "recursive": True})
rows = assets.get("assets") or assets.get("results") or []
names = sorted({(r.get("name") or r.get("asset_name")) for r in rows if isinstance(r, dict)}
               or {r for r in rows if isinstance(r, str)})
print("LedgeClimbing 자산 %d개" % len(names))

report = {}
for i, nm in enumerate(names):
    path = "%s/%s" % (DIR, nm)
    info = anim("get_sequence_info", {"asset_path": path})
    if "_ERR" in info or "skeleton" not in info:
        continue   # 시퀀스 아닌 자산(BS 등) 스킵
    mods = anim("list_anim_modifiers", {"asset_path": path})
    mlist = mods.get("modifiers") or []
    curves = anim("list_curves", {"asset_path": path})
    have = {c["name"]: c for c in (curves.get("curves") or [])}

    keys = {}
    for cn in CURVES:
        if cn not in have:
            continue
        k = anim("get_curve_keys", {"asset_path": path, "curve_name": cn})
        ks = k.get("keys") or k.get("curve_keys") or []
        keys[cn] = [[round(float(x.get("time", 0)), 4), round(float(x.get("value", 0)), 4)] for x in ks]

    report[nm] = {
        "duration": info.get("duration"),
        "num_frames": info.get("num_frames"),
        "modifiers": [{"class": m.get("class") or m.get("modifier_class") or m.get("name"),
                       "props": {k: v for k, v in (m.get("properties") or {}).items()}} for m in mlist],
        "mod_count": len(mlist),
        "curves": keys,
        "curve_names_all": sorted(have.keys()),
    }
    if (i + 1) % 20 == 0:
        print("  ... %d/%d" % (i + 1, len(names)))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)

# ── 요약 ──────────────────────────────────────────────────────────
seqs = report
print("\n시퀀스 %d개 감사 완료 -> %s" % (len(seqs), OUT))

dupe = {n: d["mod_count"] for n, d in seqs.items() if d["mod_count"] > 1}
nomod = [n for n, d in seqs.items() if d["mod_count"] == 0]
mod_classes = {}
for n, d in seqs.items():
    for m in d["modifiers"]:
        mod_classes[m["class"]] = mod_classes.get(m["class"], 0) + 1

print("\n[모디파이어 스택]")
print("  클래스별 개수: %s" % mod_classes)
print("  모디파이어 0개: %d종" % len(nomod))
if nomod:
    print("    %s" % ", ".join(sorted(nomod)[:12]) + (" ..." if len(nomod) > 12 else ""))
print("  🔴 중복(2개 이상): %d종" % len(dupe))
for n, c in sorted(dupe.items(), key=lambda x: -x[1])[:15]:
    print("    %-52s x%d" % (n, c))

print("\n[커브 보유]")
cnt = {}
for n, d in seqs.items():
    for c in d["curves"]:
        cnt[c] = cnt.get(c, 0) + 1
for c in CURVES:
    print("  %-22s %3d종" % (c, cnt.get(c, 0)))

print("\n[PRESERVE 후보 — 메모리상 수동튜닝 이력]")
for n in ("P_Player_Ledge_Move_ShortL_Wallless", "P_Player_Ledge_Move_ShortR_Wallless"):
    d = seqs.get(n)
    if not d:
        print("  %s : 없음" % n)
        continue
    print("  %s (mod=%d)" % (n, d["mod_count"]))
    for c in ("ledge_hand_ik_l", "ledge_hand_ik_r", "ledge_pelvis_spring"):
        print("     %-22s %s" % (c, d["curves"].get(c)))
