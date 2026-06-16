"""PSD_GroundMoving 의 모든 등록 클립에 PoseSearchBranchIn 을 [0, 전체길이] 로 보장.

배경 (2026-06-15 사용자 확인): PoseSearchBranchIn 노티파이가 클립 처음(0)부터 끝까지
깔려 있어야 PSD 가 그 클립을 Loop 로 처리한다. PSD_GroundMoving 의 모션은 전부 연속
loop/arc 라 모두 full-span BranchIn 이어야 맞다. 일부 엔트리가 누락되어 chatter/덜컹 유발.

정책:
  - BranchIn 0개  -> 신규 추가 [0, len]
  - BranchIn 1개  -> 시작!=0 또는 끝<len-EPS 이면 [0,len] 으로 재설정, 이미 풀이면 보존
  - BranchIn 2개+ -> 스킵 + 보고 (수동 확인. 풀스팬 합치기는 위험)

사용:
  py scripts/psd_groundmoving_branchin_full.py            # 드라이런 (변경 안 함)
  py scripts/psd_groundmoving_branchin_full.py --apply    # 적용 + 저장 + 재인덱싱

로그: scripts/_psd_groundmoving_branchin.log
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
from pathlib import Path

URL = "http://localhost:9316/mcp"
PSD = "/Game/Art/Character/PC/PC_01/MotionMatching/PSD/PSD_GroundMoving"
NOTIFY_CLASS = "AnimNotifyState_PoseSearchBranchIn"
NOTIFY_NAME = "PoseSearchBranchIn"   # get_sequence_notifies 가 반환하는 name
EPS = 0.05                            # 끝이 len 에 이만큼 못 미치면 연장
TRACK = "1"
LOG = Path(__file__).parent / "_psd_groundmoving_branchin.log"
APPLY = "--apply" in sys.argv


def call(tool: str, action: str, params: dict, timeout: int = 120):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(txt[:160])
    try:
        return json.loads(txt)
    except Exception:
        return txt


def log(msg: str):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def psd_clip_packages() -> list[str]:
    """PSD_GroundMoving 의 DatabaseAnimationAssets 에서 AnimAsset 경로(package) 추출."""
    r = call("blueprint_query", "get_cdo_properties", {"asset_path": PSD})
    val = next((p.get("value") for p in r.get("properties", [])
                if p.get("name") in ("DatabaseAnimationAssets", "AnimationAssets")), None)
    s = val if isinstance(val, str) else json.dumps(val, ensure_ascii=False)
    pkgs = []
    for m in re.finditer(r'"AnimAsset"\s*:\s*"([^"]+)"', s):
        obj = m.group(1)                 # /Game/.../Name.Name
        pkg = obj.split(".")[0]          # package path
        if pkg not in pkgs:
            pkgs.append(pkg)
    return pkgs


def branchins(path: str) -> list[dict]:
    nots = call("animation_query", "get_sequence_notifies", {"asset_path": path}).get("notifies", [])
    return [n for n in nots if n.get("name") == NOTIFY_NAME]


def main():
    log(f"=== PSD_GroundMoving BranchIn full-span {'APPLY' if APPLY else 'DRYRUN'} ===")
    pkgs = psd_clip_packages()
    log(f"PSD 등록 클립 {len(pkgs)}개")
    plan_add, plan_fix, ok, multi, err = [], [], [], [], []
    changed_paths = []

    for p in pkgs:
        name = p.split("/")[-1]
        try:
            dur = round(float(call("animation_query", "get_sequence_info", {"asset_path": p})["duration"]), 3)
            bis = branchins(p)
            if len(bis) == 0:
                plan_add.append((p, name, dur))
            elif len(bis) == 1:
                t = round(float(bis[0]["time"]), 3)
                d = round(float(bis[0]["duration"]), 3)
                end = round(t + d, 3)
                if t > 0.001 or end < dur - EPS:
                    plan_fix.append((p, name, dur, t, d, bis[0]["index"]))
                else:
                    ok.append(f"{name}: 이미 풀스팬 [0,{d}] (len {dur})")
            else:
                multi.append(f"{name}: BranchIn {len(bis)}개 — 수동")
        except Exception as e:
            err.append(f"{name}: ERROR {str(e)[:90]}")

    log(f"\n[계획] 신규추가 {len(plan_add)} / 풀스팬재설정 {len(plan_fix)} / 이미정상 {len(ok)} / 다중(스킵) {len(multi)} / 오류 {len(err)}")
    for p, name, dur in plan_add:
        log(f"  ADD  {name}: [0, {dur}]")
    for p, name, dur, t, d, idx in plan_fix:
        log(f"  FIX  {name}: [{t}, +{d}] -> [0, {dur}]")
    for s in ok:
        log(f"  OK   {s}")
    for s in multi:
        log(f"  MULTI {s}")
    for s in err:
        log(f"  ERR  {s}")

    if not APPLY:
        log("\n드라이런 종료. 적용하려면 --apply.")
        return

    log("\n=== 적용 시작 ===")
    for p, name, dur in plan_add:
        try:
            call("animation_query", "add_notify_state",
                 {"asset_path": p, "notify_class": NOTIFY_CLASS,
                  "time": 0.0, "duration": dur, "track_name": TRACK})
            changed_paths.append(p)
            log(f"  ADDED {name}: [0, {dur}]")
        except Exception as e:
            log(f"  ADD-FAIL {name}: {str(e)[:90]}")
    for p, name, dur, t, d, idx in plan_fix:
        try:
            call("animation_query", "set_notify_time",
                 {"asset_path": p, "notify_index": idx, "new_time": 0.0})
            # 시간 변경 후 인덱스 재정렬 가능 -> 재조회
            bis2 = branchins(p)
            if bis2:
                call("animation_query", "set_notify_duration",
                     {"asset_path": p, "notify_index": bis2[0]["index"], "new_duration": dur})
            changed_paths.append(p)
            log(f"  FIXED {name}: -> [0, {dur}]")
        except Exception as e:
            log(f"  FIX-FAIL {name}: {str(e)[:90]}")

    # 저장
    save_fail = []
    for p in changed_paths:
        try:
            call("editor_query", "save_asset", {"asset_path": p})
        except Exception:
            save_fail.append(p)
    log(f"저장: {len(changed_paths)-len(save_fail)}/{len(changed_paths)} (실패 {len(save_fail)})")

    # 재인덱싱
    try:
        res = call("animation_query", "rebuild_pose_search_index", {"asset_path": PSD}, timeout=300)
        log(f"REINDEX PSD_GroundMoving: {res.get('result')} poses={res.get('total_poses')}")
    except Exception as e:
        log(f"REINDEX-FAIL: {str(e)[:120]}")
    for p in save_fail:
        log(f"  SAVE-FAIL {p}")


if __name__ == "__main__":
    main()
