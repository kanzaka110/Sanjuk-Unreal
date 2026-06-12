"""
AM_SBBakePhaseCurveFromFootstepNotifies (FootSync 기준) 일괄 재적용 + 저장.

에디터 '전체 적용' 버튼 행(2026-06-11) 대체용 제어형 배치:
  - 클립당: apply_anim_modifier -> save_asset -> 진행 로그 1줄
  - 재개 가능: PROGRESS 파일에 기록된 done 항목은 스킵
  - 저장 실패해도 계속 진행 (말미에 실패 목록 요약 — 수동 Ctrl+S 대상)

실행:  py scripts/batch_rebake_phase_footsync.py
진행:  scripts/_progress_rebake_phase.log (tail로 확인)
"""
import json
import time
import urllib.request
from pathlib import Path

URL = "http://localhost:9316/mcp"
HEALTH = "http://localhost:9316/health"
ROOT = "/Game/Art/Character/PC/PC_01/Animation/Body"
MODIFIER_CLASS = "AM_SBBakePhaseCurveFromFootstepNotifies_C"
PROGRESS = Path(__file__).parent / "_progress_rebake_phase.log"


def call(tool: str, action: str, params: dict, timeout: int = 120):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(txt[:200])
    return json.loads(txt)


def log(msg: str):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(PROGRESS, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def wait_health(max_wait_s: int = 900):
    t0 = time.time()
    while time.time() - t0 < max_wait_s:
        try:
            urllib.request.urlopen(HEALTH, timeout=5)
            log("Monolith LIVE")
            return True
        except Exception:
            time.sleep(10)
    return False


def list_all_sequences() -> list[str]:
    paths, offset = [], 0
    while True:
        r = call("editor_query", "list_assets",
                 {"directory": ROOT, "class_filter": "AnimSequence",
                  "recursive": True, "offset": offset})
        for a in r.get("assets", []):
            paths.append(a["package"])
        offset += r.get("count", 0)
        if offset >= r.get("total", 0) or r.get("count", 0) == 0:
            break
    return paths


def main():
    if not wait_health():
        log("FATAL: Monolith 미응답 (15분)")
        return

    done = set()
    if PROGRESS.exists():
        for ln in PROGRESS.read_text(encoding="utf-8").splitlines():
            if " OK " in ln or " SAVED " in ln:
                done.add(ln.split()[-1])

    seqs = list_all_sequences()
    log(f"대상 폴더 스캔: AnimSequence {len(seqs)}개 (이미 완료 {len(done)}개 스킵)")

    applied, saved, save_fail, skipped, no_mod, errors = 0, 0, [], 0, 0, []
    t_start = time.time()

    for i, p in enumerate(seqs):
        if p in done:
            skipped += 1
            continue
        try:
            mods = call("animation_query", "list_anim_modifiers", {"asset_path": p})
            classes = [m.get("class") for m in mods.get("modifiers", [])]
            if MODIFIER_CLASS not in classes:
                no_mod += 1
                continue
            call("animation_query", "apply_anim_modifier",
                 {"asset_path": p, "modifier_class": MODIFIER_CLASS}, timeout=300)
            applied += 1
            try:
                call("editor_query", "save_asset", {"asset_path": p})
                saved += 1
                log(f"SAVED ({applied}) {p}")
            except Exception as e:
                save_fail.append(p)
                log(f"OK (save실패: {str(e)[:60]}) {p}")
        except Exception as e:
            errors.append((p, str(e)[:100]))
            log(f"ERROR {str(e)[:80]} {p}")
        if applied and applied % 25 == 0:
            rate = applied / max(1, time.time() - t_start) * 60
            log(f"--- 진행 {applied} 적용 / {rate:.0f}개·분 / 스캔 {i+1}/{len(seqs)}")

    log("=" * 50)
    log(f"완료: 적용 {applied}, 저장 {saved}, 저장실패 {len(save_fail)}, "
        f"모디파이어없음 {no_mod}, 기완료스킵 {skipped}, 에러 {len(errors)}")
    if save_fail:
        log("수동 저장 필요(Ctrl+S):")
        for p in save_fail:
            log(f"  - {p}")
    for p, e in errors[:20]:
        log(f"  ERR {p}: {e}")


if __name__ == "__main__":
    main()
