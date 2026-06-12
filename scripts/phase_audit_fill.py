"""
PSD 멤버 시퀀스 phase 커브 감사 + 누락분 생성.

기준: 7개 PSD에 등록된 AnimSequence = 매칭 참여 = phase 필수.
  - phase 있음               -> OK
  - 없음 + FootSync 노티 있음 -> apply_anim_modifier 시도, 실패 시 직접 베이크
                                (FootSync Right=0, Left 직전 -1 / Left=+1, 모디파이어 컨벤션)
  - 없음 + FootSync 도 없음   -> 생성 불가 보고 (노티파이 작업 필요)

마무리: 변경분 저장 + PSD 재인덱싱. 로그: scripts/_phase_audit.log
"""
import json
import time
import urllib.request
from pathlib import Path

URL = "http://localhost:9316/mcp"
PSD_DIR = "/Game/Art/Character/PC/PC_01/MotionMatching/PSD"
LOG = Path(__file__).parent / "_phase_audit.log"
MODIFIER_CLASS = "AM_SBBakePhaseCurveFromFootstepNotifies_C"


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


def psd_members() -> list[str]:
    psds = call("editor_query", "list_assets",
                {"directory": PSD_DIR, "class_filter": "PoseSearchDatabase"})["assets"]
    members = set()
    for a in psds:
        d = call("animation_query", "get_pose_search_database", {"asset_path": a["package"]})
        for s in d.get("sequences", []):
            if s.get("asset_class") == "AnimSequence" and s.get("animation"):
                members.add(s["animation"].split(".")[0])
    return sorted(members)


def direct_bake(p: str, foot_syncs: list[tuple[str, float]]) -> int:
    """모디파이어 컨벤션 그대로 phase 키 생성: R=0, L직전 -1 / L=+1."""
    keys = []
    for track, t in sorted(foot_syncs, key=lambda x: x[1]):
        if "Right" in track:
            keys.append({"time": round(t, 4), "value": 0.0, "interp": "linear"})
        else:
            keys.append({"time": round(t - 0.01, 4), "value": -1.0, "interp": "linear"})
            keys.append({"time": round(t, 4), "value": 1.0, "interp": "linear"})
    call("animation_query", "set_curve_keys",
         {"asset_path": p, "curve_name": "phase", "keys_json": json.dumps(keys)})
    return len(keys)


def main():
    members = psd_members()
    log(f"PSD 멤버 AnimSequence: {len(members)}개")

    ok, fixed_mod, fixed_bake, impossible, errors = 0, 0, 0, [], []
    changed = []

    for p in members:
        name = p.split("/")[-1]
        try:
            curves = call("animation_query", "get_sequence_curves", {"asset_path": p})["curves"]
            has_phase = any(c["name"].lower() == "phase" and c["num_keys"] >= 2 for c in curves)
            if has_phase:
                ok += 1
                continue
            nots = call("animation_query", "get_sequence_notifies", {"asset_path": p})["notifies"]
            fs = [(n["track_name"], n["time"]) for n in nots if "FootSync" in n["track_name"]]
            if not fs:
                impossible.append(name)
                continue
            # 1차: 모디파이어 적용 (등록돼 있으면 정식 경로)
            mods = call("animation_query", "list_anim_modifiers", {"asset_path": p})
            classes = [m.get("class") for m in mods.get("modifiers", [])]
            if MODIFIER_CLASS in classes:
                call("animation_query", "apply_anim_modifier",
                     {"asset_path": p, "modifier_class": MODIFIER_CLASS}, timeout=300)
                log(f"MOD   {name}: 모디파이어 재적용")
                fixed_mod += 1
            else:
                n = direct_bake(p, fs)
                log(f"BAKE  {name}: FootSync {len(fs)}개 -> phase {n}키 직접 베이크 (모디파이어 미등록)")
                fixed_bake += 1
            changed.append(p)
            try:
                call("editor_query", "save_asset", {"asset_path": p})
            except Exception:
                log(f"  save 실패(수동 필요): {name}")
        except Exception as e:
            errors.append(f"{name}: {str(e)[:80]}")

    log("=" * 50)
    log(f"감사 결과: 정상 {ok} / 모디파이어적용 {fixed_mod} / 직접베이크 {fixed_bake} / "
        f"생성불가 {len(impossible)} / 에러 {len(errors)}")
    for n in impossible:
        log(f"  생성불가(FootSync 없음): {n}")
    for e in errors:
        log(f"  ERR {e}")

    if changed:
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
