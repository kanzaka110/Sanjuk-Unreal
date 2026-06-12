"""
Turn 시리즈 16개에 FootSync 노티파이 + phase 커브 생성.

경로:
  1차: AM_SBFootSyncNotifies_C 적용 시도 (본 모션 분석 — 정식 파이프라인)
  폴백: Footstep 노티파이 +0.09s 에 AN_SBFootSyncNotify 직접 추가
        (locomotion 전수 실측 오프셋, 2026-06-11)
이후: FootSync 기준 phase 직접 베이크 (R=0, L직전 -1 / L=+1) -> 저장 -> PSD 재인덱싱.
로그: scripts/_turn_footsync.log
"""
import json
import time
import urllib.request
from pathlib import Path

URL = "http://localhost:9316/mcp"
PSD_DIR = "/Game/Art/Character/PC/PC_01/MotionMatching/PSD"
LOG = Path(__file__).parent / "_turn_footsync.log"
SYNC_MOD = "AM_SBFootSyncNotifies_C"
SYNC_CLASS = "AN_SBFootSyncNotify_C"
OFFSET = 0.09

TURN_NAMES = [
    f"P_Player_{g}_Turn_{a}_{s}"
    for g in ("Stand", "Fist_Battle")
    for a in ("045", "090", "135", "180")
    for s in ("L", "R")
]


def call(tool: str, action: str, params: dict, timeout: int = 180):
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


def resolve(name: str) -> str | None:
    r = call("project_query", "search", {"query": name, "limit": 5})
    for x in r.get("results", []):
        if x.get("asset_class") == "AnimSequence" and x["asset_path"].endswith(name):
            return x["asset_path"]
    return None


def get_footsyncs(p: str) -> list[tuple[str, float]]:
    nots = call("animation_query", "get_sequence_notifies", {"asset_path": p})["notifies"]
    return [(n["track_name"], n["time"]) for n in nots if "FootSync" in n["track_name"]]


def bake_phase(p: str, fs: list[tuple[str, float]]):
    keys = []
    for track, t in sorted(fs, key=lambda x: x[1]):
        if "Right" in track:
            keys.append({"time": round(t, 4), "value": 0.0, "interp": "linear"})
        else:
            keys.append({"time": round(t - 0.01, 4), "value": -1.0, "interp": "linear"})
            keys.append({"time": round(t, 4), "value": 1.0, "interp": "linear"})
    try:
        call("animation_query", "add_curve", {"asset_path": p, "curve_name": "phase"})
    except Exception:
        pass
    call("animation_query", "set_curve_keys",
         {"asset_path": p, "curve_name": "phase", "keys_json": json.dumps(keys)})
    return len(keys)


def main():
    done, errors = 0, []
    for name in TURN_NAMES:
        try:
            p = resolve(name)
            if not p:
                errors.append(f"{name}: 경로 미발견")
                continue
            fs = get_footsyncs(p)
            src = "기존"
            if not fs:
                # 1차: 모디파이어 적용
                try:
                    call("animation_query", "apply_anim_modifier",
                         {"asset_path": p, "modifier_class": SYNC_MOD}, timeout=300)
                    fs = get_footsyncs(p)
                    src = "모디파이어"
                except Exception:
                    fs = []
                if not fs:
                    # 폴백: Footstep +0.09
                    nots = call("animation_query", "get_sequence_notifies",
                                {"asset_path": p})["notifies"]
                    steps = [(n["track_name"], n["time"]) for n in nots
                             if "Footstep" in n["track_name"]]
                    if not steps:
                        errors.append(f"{name}: Footstep 도 없음 — 생성 불가")
                        continue
                    for track, t in steps:
                        side = "Left" if "Left" in track else "Right"
                        call("animation_query", "add_notify",
                             {"asset_path": p, "notify_class": SYNC_CLASS,
                              "time": round(t + OFFSET, 4),
                              "track_name": f"FootSync {side}"})
                    fs = get_footsyncs(p)
                    src = "Footstep+0.09 폴백"
            if not fs:
                errors.append(f"{name}: FootSync 생성 실패")
                continue
            nk = bake_phase(p, fs)
            log(f"OK    {name}: FootSync {len(fs)}개({src}) -> phase {nk}키")
            done += 1
            try:
                call("editor_query", "save_asset", {"asset_path": p})
            except Exception:
                log(f"  save 실패(수동 필요): {name}")
        except Exception as e:
            errors.append(f"{name}: {str(e)[:80]}")

    log("=" * 50)
    log(f"완료 {done}/{len(TURN_NAMES)}, 에러 {len(errors)}")
    for e in errors:
        log(f"  ERR {e}")

    psds = call("editor_query", "list_assets",
                {"directory": PSD_DIR, "class_filter": "PoseSearchDatabase"})["assets"]
    for a in psds:
        try:
            res = call("animation_query", "rebuild_pose_search_index",
                       {"asset_path": a["package"]}, timeout=300)
            log(f"REINDEX {a['name']}: {res.get('result')} poses={res.get('total_poses')}")
        except Exception as e:
            log(f"REINDEX-FAIL {a['name']}: {str(e)[:80]}")


if __name__ == "__main__":
    main()
