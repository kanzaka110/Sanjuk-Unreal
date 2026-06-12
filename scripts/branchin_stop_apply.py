"""
PoseSearchBranchIn Stop 클립 일괄 정비 (드라이런 branchin_stop_dryrun.py 의 적용 버전).

정책 (2026-06-12 사용자 승인):
  - BranchIn 0개  -> 신규 추가: 시작=max(0, t0-0.43), 끝=min(len, t0+0.30)
  - 가드 8개 (Fist_Guard_Walk_Stop) -> 풀 공식으로 시작+유지 재설정
  - 그 외 1개 보유 -> 끝이 t0+0.30 에 0.05s 이상 못 미치면 유지시간만 연장 (시작 보존)
  - 그 외 -> 보존 (잘 동작 중, 회귀 방지)
  - BranchIn 2개+ / t0 산출 불가 -> 스킵 + 보고

마무리: 변경 클립 저장 + PSD 전체 재인덱싱.
로그: scripts/_branchin_stop_apply.log
"""
import json
import time
import urllib.request
from pathlib import Path

URL = "http://localhost:9316/mcp"
ROOT = "/Game/Art/Character/PC/PC_01/Animation/Body"
PSD_DIR = "/Game/Art/Character/PC/PC_01/MotionMatching/PSD"
LOG = Path(__file__).parent / "_branchin_stop_apply.log"
NOTIFY_CLASS = "AnimNotifyState_PoseSearchBranchIn"
PRE, POST = 0.43, 0.30


def call(tool: str, action: str, params: dict, timeout: int = 120):
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


def log(msg: str):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


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
    if peak_v < 30:
        return None
    peak_t = next(k["time"] for k in keys if k["value"] == peak_v)
    for k in keys:
        if k["time"] > peak_t and k["value"] < 5:
            return k["time"]
    return None


def main():
    seqs = list_stop_sequences()
    added, adjusted, extended, kept, skipped = 0, 0, 0, 0, []
    save_fail = []

    for p in seqs:
        name = p.split("/")[-1]
        try:
            try:
                spd = call("animation_query", "get_curve_keys",
                           {"asset_path": p, "curve_name": "MoveData_Speed"})["keys"]
            except Exception:
                skipped.append(f"{name}: MoveData_Speed 없음")
                continue
            t0 = find_t_zero(spd)
            if t0 is None:
                skipped.append(f"{name}: 속도0 산출 불가")
                continue
            info = call("animation_query", "get_sequence_info", {"asset_path": p})
            clip_len = info["duration"]
            rec_start = max(0.0, round(t0 - PRE, 3))
            rec_end = min(clip_len, round(t0 + POST, 3))
            rec_dur = round(rec_end - rec_start, 3)

            nots = call("animation_query", "get_sequence_notifies", {"asset_path": p})["notifies"]
            bis = [(n["index"], n["time"], n["duration"]) for n in nots
                   if n["name"] == "PoseSearchBranchIn"]

            changed = False
            if len(bis) == 0:
                call("animation_query", "add_notify_state",
                     {"asset_path": p, "notify_class": NOTIFY_CLASS,
                      "time": rec_start, "duration": rec_dur, "track_name": "1"})
                log(f"ADD   {name}: 시작 {rec_start} / 유지 {rec_dur}")
                added += 1
                changed = True
            elif len(bis) == 1:
                idx, cur_start, cur_dur = bis[0]
                cur_end = cur_start + cur_dur
                if "Fist_Guard_Walk_Stop" in name:
                    call("animation_query", "set_notify_time",
                         {"asset_path": p, "notify_index": idx, "new_time": rec_start})
                    # 시간 변경 후 인덱스가 재정렬될 수 있어 재조회
                    nots2 = call("animation_query", "get_sequence_notifies",
                                 {"asset_path": p})["notifies"]
                    idx2 = next(n["index"] for n in nots2
                                if n["name"] == "PoseSearchBranchIn")
                    call("animation_query", "set_notify_duration",
                         {"asset_path": p, "notify_index": idx2, "new_duration": rec_dur})
                    log(f"FULL  {name}: {cur_start:.3f}/{cur_dur:.3f} -> {rec_start}/{rec_dur}")
                    adjusted += 1
                    changed = True
                elif cur_end < rec_end - 0.05:
                    new_dur = round(rec_end - cur_start, 3)
                    call("animation_query", "set_notify_duration",
                         {"asset_path": p, "notify_index": idx, "new_duration": new_dur})
                    log(f"EXT   {name}: 유지 {cur_dur:.3f} -> {new_dur} (시작 {cur_start:.3f} 보존)")
                    extended += 1
                    changed = True
                else:
                    kept += 1
            else:
                skipped.append(f"{name}: BranchIn {len(bis)}개 — 수동 확인")
                continue

            if changed:
                try:
                    call("editor_query", "save_asset", {"asset_path": p})
                except Exception:
                    save_fail.append(p)
        except Exception as e:
            skipped.append(f"{name}: ERROR {str(e)[:80]}")

    log("=" * 50)
    log(f"완료: 신규추가 {added}, 풀공식 {adjusted}, 끝연장 {extended}, "
        f"보존 {kept}, 스킵 {len(skipped)}, 저장실패 {len(save_fail)}")
    for s in skipped:
        log(f"  SKIP {s}")
    for p in save_fail:
        log(f"  SAVE-FAIL {p}")

    # PSD 전체 재인덱싱
    r = call("editor_query", "list_assets",
             {"directory": PSD_DIR, "class_filter": "PoseSearchDatabase"})
    for a in r.get("assets", []):
        pkg = a["package"]
        try:
            res = call("animation_query", "rebuild_pose_search_index",
                       {"asset_path": pkg}, timeout=300)
            log(f"REINDEX {pkg.split('/')[-1]}: {res.get('result')} poses={res.get('total_poses')}")
        except Exception as e:
            log(f"REINDEX-FAIL {pkg.split('/')[-1]}: {str(e)[:80]}")


if __name__ == "__main__":
    main()
