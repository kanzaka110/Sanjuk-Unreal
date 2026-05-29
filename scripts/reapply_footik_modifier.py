"""
AM_SBFootIKWeight 일괄 재적용 마이그레이션.

대상:
  /Game/Art/Character/PC/PC_01/Animation/Body/ 하위 AnimSequence 중
  AM_SBFootIKWeight 모디파이어가 이미 적용된 것만.

목적:
  어제(2026-05-28) 추가된 RateLimitSingleCurve 5-pass 로직을 기존 anim에
  일괄 반영. ApplyModifier가 본 트랙에서 4 curve를 새로 산출하므로 멱등.

실행 (UE 5.7 에디터 Python 콘솔):
  exec(open(r"C:\\Dev\\Sanjuk-Unreal\\scripts\\reapply_footik_modifier.py",
            encoding="utf-8").read(), {"__name__": "__main__"})

옵션:
  DRY_RUN=True  -> 대상 목록만 출력 (적용/저장 안 함). 첫 실행은 무조건 이걸로.
  DRY_RUN=False -> 실제 적용 + 저장. 사전에 백업 JSON 생성.

백업:
  dumps/footik_reapply/backup_<timestamp>.json
  변경 전 4 curve 키 dump -> 복원 스크립트로 롤백 가능.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import unreal

# ============================ Config ============================
TARGET_DIR: str = "/Game/Art/Character/PC/PC_01/Animation/Body"
TARGET_MODIFIER_CLASS_NAME: str = "AM_SBFootIKWeight_C"
CURVES: Tuple[str, ...] = (
    "DisableFootLock_L",
    "DisableFootLock_R",
    "DisableFootIK_L",
    "DisableFootIK_R",
)
BACKUP_DIR: str = r"C:\Dev\Sanjuk-Unreal\dumps\footik_reapply"
DRY_RUN: bool = False
SAVE_ASSETS: bool = True

RCT_FLOAT = unreal.RawCurveTrackTypes.RCT_FLOAT


# ============================ Asset scan ============================
def list_anim_sequences(root_dir: str) -> List[str]:
    """root_dir 하위 모든 AnimSequence 의 package path 반환 (`/Game/.../Foo`)."""
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    datas = ar.get_assets_by_path(root_dir, recursive=True)
    out: List[str] = []
    for ad in datas:
        try:
            cls_name = str(ad.asset_class_path.asset_name)
        except AttributeError:
            cls_name = str(ad.asset_class)
        if cls_name == "AnimSequence":
            out.append(str(ad.package_name))
    return out


def has_target_modifier(seq: unreal.AnimSequence, target_class_name: str) -> Optional[Any]:
    """
    seq 에 target_class_name 모디파이어 인스턴스가 있으면 반환, 없으면 None.
    SB2 빌드 API (probe 2026-05-29 확정):
      seq -> AnimationModifiersAssetUserData -> animation_modifier_instances
    """
    try:
        aud = seq.get_asset_user_data_of_class(unreal.AnimationModifiersAssetUserData)
    except Exception as e:
        unreal.log_warning(f"  get_asset_user_data fail: {e}")
        return None
    if aud is None:
        return None
    try:
        instances = aud.get_editor_property("animation_modifier_instances")
    except Exception as e:
        unreal.log_warning(f"  read animation_modifier_instances fail: {e}")
        return None
    for inst in instances:
        if inst and inst.get_class().get_name() == target_class_name:
            return inst
    return None


# ============================ Curve dump ============================
def dump_curves(seq: unreal.AnimSequence, curves: Tuple[str, ...]) -> Dict[str, List[Tuple[float, float]]]:
    out: Dict[str, List[Tuple[float, float]]] = {}
    for c in curves:
        if not unreal.AnimationLibrary.does_curve_exist(seq, c, RCT_FLOAT):
            out[c] = []
            continue
        try:
            times, values = unreal.AnimationLibrary.get_float_keys(seq, c)
            out[c] = [(float(t), float(v)) for t, v in zip(times, values)]
        except Exception as e:
            unreal.log_warning(f"  curve dump fail [{c}]: {e}")
            out[c] = []
    return out


def max_delta(keys: List[Tuple[float, float]]) -> float:
    if len(keys) < 2:
        return 0.0
    return max(abs(keys[i + 1][1] - keys[i][1]) for i in range(len(keys) - 1))


# ============================ Modifier apply ============================
def apply_modifier(seq: unreal.AnimSequence, modifier_instance: Any) -> bool:
    """
    SB2 빌드 (probe 2026-05-29 확정):
      modifier.call_method("ApplyModifier", (seq,))
      -> AM_SBFootIKWeight_C BP 함수 ApplyModifier 직접 호출
      -> ProcessCurveDatas + SmoothStep + RateLimitSingleCurve x5 실행
      -> 4 curve 재산출, AnimationCompression 재빌드

    참고:
      - on_apply/on_revert 직접 호출은 BlueprintImplementableEvent 라 silent fail
      - UE 5.7 stock 의 ApplyToAnimationSequence 는 SB2 미노출
    """
    try:
        modifier_instance.call_method("ApplyModifier", (seq,))
        return True
    except Exception as e:
        unreal.log_error(f"  ApplyModifier fail: {type(e).__name__}: {e}")
        return False


# ============================ Main ============================
def main() -> None:
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    unreal.log("=" * 78)
    unreal.log(f"AM_SBFootIKWeight Reapply  (DRY_RUN={DRY_RUN}, SAVE={SAVE_ASSETS})")
    unreal.log(f"Scan: {TARGET_DIR}")
    unreal.log(f"Filter modifier: {TARGET_MODIFIER_CLASS_NAME}")
    unreal.log("=" * 78)

    all_seqs = list_anim_sequences(TARGET_DIR)
    unreal.log(f"AnimSequence found: {len(all_seqs)}")

    candidates: List[Tuple[str, Any]] = []
    for p in all_seqs:
        seq = unreal.load_asset(p)
        if not seq:
            unreal.log_warning(f"  load fail: {p}")
            continue
        inst = has_target_modifier(seq, TARGET_MODIFIER_CLASS_NAME)
        if inst is not None:
            candidates.append((p, inst))

    unreal.log(f"Targets (has {TARGET_MODIFIER_CLASS_NAME}): {len(candidates)}")
    for p, _ in candidates:
        unreal.log(f"  - {p}")

    if DRY_RUN:
        unreal.log("DRY_RUN=True -> 적용 안 함. 결과 확인 후 DRY_RUN=False 로 재실행.")
        return

    if not candidates:
        unreal.log("대상 없음. 종료.")
        return

    backup: Dict[str, Any] = {
        "timestamp": ts,
        "target_dir": TARGET_DIR,
        "modifier_class": TARGET_MODIFIER_CLASS_NAME,
        "anims": {},
    }
    report: List[Dict[str, Any]] = []

    for p, inst in candidates:
        seq = unreal.load_asset(p)
        if not seq:
            continue

        before = dump_curves(seq, CURVES)
        md_before = {c: round(max_delta(k), 3) for c, k in before.items()}
        backup["anims"][p] = before

        ok = apply_modifier(seq, inst)
        after = dump_curves(seq, CURVES) if ok else {}
        md_after = {c: round(max_delta(k), 3) for c, k in after.items()}

        save_status = "SKIPPED"
        if ok and SAVE_ASSETS:
            try:
                if unreal.EditorAssetLibrary.save_asset(p, only_if_is_dirty=True):
                    save_status = "SAVED"
                else:
                    save_status = "NEEDS_CHECKOUT"
            except Exception as e:
                save_status = "SAVE_ERROR"
                unreal.log_warning(f"  save raised [{p}]: {type(e).__name__}: {e}")

        apply_tag = "OK" if ok else "FAIL"
        report.append(
            {
                "anim_path": p,
                "anim_name": p.split("/")[-1],
                "apply": apply_tag,
                "save": save_status,
                "md_before": md_before,
                "md_after": md_after,
            }
        )
        unreal.log(f"[apply={apply_tag} save={save_status}] {p}")
        unreal.log(f"      md_before={md_before}")
        unreal.log(f"      md_after ={md_after}")

    # Backup JSON
    backup_path = os.path.join(BACKUP_DIR, f"backup_{ts}.json")
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(backup, f, indent=2)
    unreal.log(f"BACKUP: {backup_path}")

    # Aggregate
    apply_failed = [r["anim_path"] for r in report if r["apply"] != "OK"]
    saved = [r["anim_path"] for r in report if r["save"] == "SAVED"]
    needs_checkout = [
        r["anim_path"] for r in report if r["save"] in ("NEEDS_CHECKOUT", "SAVE_ERROR")
    ]

    # needs_checkout 리스트 -> 텍스트 파일
    if needs_checkout:
        nc_path = os.path.join(BACKUP_DIR, f"needs_checkout_{ts}.txt")
        with open(nc_path, "w", encoding="utf-8") as f:
            for p in needs_checkout:
                f.write(p + "\n")
        unreal.log(f"NEEDS_CHECKOUT list: {nc_path}  ({len(needs_checkout)} paths)")
        unreal.log("  -> 이 경로들을 UE Content Browser 또는 P4V 에서 Check Out 후 스크립트 재실행.")
        unreal.log("  -> 모디파이어는 deterministic 하므로 재실행해도 동일 결과.")

    unreal.log("=" * 78)
    unreal.log(f"SUMMARY  total candidates: {len(report)}")
    unreal.log(f"  apply OK       : {len(report) - len(apply_failed)}")
    unreal.log(f"  apply FAIL     : {len(apply_failed)}")
    unreal.log(f"  saved          : {len(saved)}")
    unreal.log(f"  needs_checkout : {len(needs_checkout)}")
    unreal.log("=" * 78)


if __name__ == "__main__":
    main()
