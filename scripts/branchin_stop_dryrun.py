"""
PoseSearchBranchIn 최적 배치 드라이런 — Stop 클립 한정. 적용 없음(read-only).

공식 (레퍼런스 Battle_Walk_Stop_F_Lfoot 역산, 2026-06-11 도출):
    시작 = 루트속도0 시점(t0) - 0.43s   (클램프: >= 0)
    유지 = 0.73s                        (끝 = t0 + 0.30s, 클램프: <= 클립 길이)

t0 = MoveData_Speed 피크 이후 처음으로 5 미만으로 떨어지는 키 시각.

출력: scripts/_branchin_stop_dryrun.txt (표 + 이상치 목록)
"""
import json
import time
import urllib.request
from pathlib import Path

URL = "http://localhost:9316/mcp"
ROOT = "/Game/Art/Character/PC/PC_01/Animation/Body"
OUT = Path(__file__).parent / "_branchin_stop_dryrun.txt"

PRE = 0.43   # t0 이전 커버
POST = 0.30  # t0 이후 커버


def call(tool: str, action: str, params: dict, timeout: int = 60):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(txt[:150])
    return json.loads(txt)


def list_stop_sequences() -> list[str]:
    paths, offset = [], 0
    while True:
        r = call("editor_query", "list_assets",
                 {"directory": ROOT, "class_filter": "AnimSequence",
                  "recursive": True, "offset": offset})
        for a in r.get("assets", []):
            if "_Stop_" in a["name"] or a["name"].endswith("_Stop"):
                paths.append(a["package"])
        offset += r.get("count", 0)
        if offset >= r.get("total", 0) or r.get("count", 0) == 0:
            break
    return sorted(paths)


def find_t_zero(keys: list[dict]) -> float | None:
    peak_v = max(k["value"] for k in keys)
    if peak_v < 30:  # 보행 구간이 없는 클립 (정지 전용/이상치)
        return None
    peak_t = next(k["time"] for k in keys if k["value"] == peak_v)
    for k in keys:
        if k["time"] > peak_t and k["value"] < 5:
            return k["time"]
    return None


def main():
    seqs = list_stop_sequences()
    rows, anomalies = [], []

    for p in seqs:
        name = p.split("/")[-1]
        try:
            nots = call("animation_query", "get_sequence_notifies", {"asset_path": p})["notifies"]
            bis = [n for n in nots if n["name"] == "PoseSearchBranchIn"]
            if len(bis) != 1:
                anomalies.append(f"{name}: BranchIn {len(bis)}개 — 수동 확인")
                continue
            bi = bis[0]
            info = call("animation_query", "get_sequence_info", {"asset_path": p})
            dur_clip = info["duration"]
            spd = call("animation_query", "get_curve_keys",
                       {"asset_path": p, "curve_name": "MoveData_Speed"})["keys"]
            t0 = find_t_zero(spd)
            if t0 is None:
                anomalies.append(f"{name}: 속도0 시점 산출 불가 (피크<30 또는 미감속)")
                continue
            rec_start = max(0.0, t0 - PRE)
            rec_end = min(dur_clip, t0 + POST)
            rec_dur = round(rec_end - rec_start, 3)
            clipped = " (끝 클램프)" if t0 + POST > dur_clip else ""
            cur_start, cur_dur = bi["time"], bi["duration"]
            d_start = rec_start - cur_start
            d_end = rec_end - (cur_start + cur_dur)
            rows.append((name, cur_start, cur_dur, round(rec_start, 3), rec_dur,
                         round(d_start, 2), round(d_end, 2), clipped))
        except Exception as e:
            anomalies.append(f"{name}: ERROR {str(e)[:60]}")

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(f"# BranchIn Stop 드라이런 {time.strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"# 공식: 시작=t0-{PRE}, 유지={PRE+POST} (t0=루트속도0)\n\n")
        f.write(f"{'클립':52s} {'현시작':>7s} {'현유지':>7s} {'권시작':>7s} {'권유지':>7s} {'Δ시작':>6s} {'Δ끝':>6s}\n")
        for r in rows:
            f.write(f"{r[0]:52s} {r[1]:7.3f} {r[2]:7.3f} {r[3]:7.3f} {r[4]:7.3f} "
                    f"{r[5]:6.2f} {r[6]:6.2f}{r[7]}\n")
        f.write(f"\n## 이상치/제외 ({len(anomalies)}건)\n")
        for a in anomalies:
            f.write(f"  - {a}\n")

    big = [r for r in rows if abs(r[5]) > 0.15 or abs(r[6]) > 0.15]
    print(f"Stop 클립 {len(seqs)}개 스캔 → 산출 {len(rows)}개, 이상치 {len(anomalies)}개")
    print(f"권장과 0.15s 이상 차이: {len(big)}개")
    print(f"상세: {OUT}")


if __name__ == "__main__":
    main()
