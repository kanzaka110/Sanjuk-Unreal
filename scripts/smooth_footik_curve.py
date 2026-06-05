"""
Smooth FootIK/FootLock disable curves on an AnimSequence via Monolith HTTP API.

Why: AM_SBFootIKWeight.RateLimitSingleCurve inserts LINEAR midpoints, which is a
mathematical no-op on a linear-interp curve (curve shape & per-frame delta unchanged).
This script does a REAL smooth: resample at frame rate -> moving average -> clamp [0,1].

Modes:
  --dry   : GET + analyze + compute, print before/after max per-frame delta. NO write. (default)
  --apply : also SET the smoothed keys back (replaces existing keys).

Backup of original keys is always written to scripts/_curve_backup_<asset>.json on GET.
"""
import sys, json, urllib.request, os

URL = "http://localhost:9316/mcp"
_pos = [a for a in sys.argv[1:] if not a.startswith("--")]
ASSET = _pos[0] if _pos else "/Game/Art/Character/PC/PC_01/Animation/Body/Walk/P_Player_Fist_Guard_Walk_Turn_R_90_Lfoot"
CURVES = ["DisableFootIK_L", "DisableFootIK_R", "DisableFootLock_L", "DisableFootLock_R"]
WINDOW = 5          # moving-average taps (odd). 3=mild, 5=medium, 7=strong
FPS = 30.0

_id = [0]
def rpc(action, params):
    _id[0] += 1
    body = json.dumps({"jsonrpc": "2.0", "method": "tools/call", "id": _id[0],
                       "params": {"name": "animation_query",
                                  "arguments": {"action": action, "params": params}}}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    raw = urllib.request.urlopen(req, timeout=30).read().decode()
    obj = json.loads(raw)
    # unwrap MCP content[].text
    if "result" in obj and isinstance(obj["result"], dict) and "content" in obj["result"]:
        txt = obj["result"]["content"][0]["text"]
        return json.loads(txt)
    return obj

def sample_linear(keys, t):
    # keys: sorted list of (time,value). piecewise linear, hold ends.
    if t <= keys[0][0]:
        return keys[0][1]
    if t >= keys[-1][0]:
        return keys[-1][1]
    lo, hi = 0, len(keys) - 1
    for i in range(len(keys) - 1):
        if keys[i][0] <= t <= keys[i + 1][0]:
            t0, v0 = keys[i]; t1, v1 = keys[i + 1]
            if t1 == t0:
                return v1
            a = (t - t0) / (t1 - t0)
            return v0 + a * (v1 - v0)
    return keys[-1][1]

def max_step(arr):
    return max((abs(arr[i] - arr[i - 1]) for i in range(1, len(arr))), default=0.0)

def moving_avg(arr, w):
    h = w // 2
    out = []
    n = len(arr)
    for i in range(n):
        s = 0.0; c = 0
        for j in range(i - h, i + h + 1):
            if 0 <= j < n:
                s += arr[j]; c += 1
        out.append(max(0.0, min(1.0, s / c)))
    return out

def main():
    apply = "--apply" in sys.argv
    fps = FPS
    # derive duration from curve keys (get_sequence_info HTTP can return empty)
    _probe = rpc("get_curve_keys", {"asset_path": ASSET, "curve_name": CURVES[2]})
    dur = max(k["time"] for k in _probe["keys"])
    nframes = int(round(dur * fps)) + 1
    times = [i / fps for i in range(nframes)]
    print(f"asset duration={dur:.3f}s fps={fps} frames={nframes} window={WINDOW} mode={'APPLY' if apply else 'DRY'}")
    print("-" * 78)
    backup = {}
    for cname in CURVES:
        r = rpc("get_curve_keys", {"asset_path": ASSET, "curve_name": cname})
        keys = [(k["time"], k["value"]) for k in r["keys"]]
        keys.sort()
        backup[cname] = r["keys"]
        before = [sample_linear(keys, t) for t in times]
        after = moving_avg(before, WINDOW)
        b, a = max_step(before), max_step(after)
        # locate worst frame
        wf = max(range(1, len(before)), key=lambda i: abs(before[i] - before[i - 1]))
        print(f"{cname:18s} keys={len(keys):3d}  maxΔ/frame  before={b:.3f}  after={a:.3f}  "
              f"(worst @ t={times[wf]:.3f}s)")
        if apply:
            new_keys = [{"time": round(t, 5), "value": round(v, 5), "interp": "linear"}
                        for t, v in zip(times, after)]
            res = rpc("set_curve_keys", {"asset_path": ASSET, "curve_name": cname,
                                          "keys_json": json.dumps(new_keys)})
            print(f"   -> set_curve_keys: {json.dumps(res)[:120]}")
    bpath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "_curve_backup_" + ASSET.rsplit("/", 1)[-1] + ".json")
    with open(bpath, "w", encoding="utf-8") as f:
        json.dump(backup, f, ensure_ascii=False, indent=1)
    print("-" * 78)
    print(f"original keys backed up -> {bpath}")
    if not apply:
        print("DRY run only. Re-run with --apply to write smoothed keys.")

if __name__ == "__main__":
    main()
