"""PC_01 AnimLayer_IK 의 PelvisSettings 3 프로필 덤프.

Monolith 조회 결과 확인된 변수 (PC_01_AnimLayer_IK 소속):
- PelvisSettingsDefault   (기본대기)
- PelvisSettingsMove      (이동)
- PelvisSettingsProne     (다운 / 누움)

타입: struct:FootPlacementPelvisSettings

실행:
  UE 에디터 > Output Log > Cmd=Python
  exec(open(r'C:/Dev/Sanjuk-Unreal/scripts/dump_footplacement_params.py').read())

결과: Output Log + Saved/Logs/PelvisSettingsDump.txt
"""
from __future__ import annotations

import os
from typing import Any

import unreal

ASSET_PATH = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK"
GEN_CLASS_PATH = f"{ASSET_PATH}.PC_01_AnimLayer_IK_C"

VARIABLES = [
    ("PelvisSettingsDefault", "기본대기"),
    ("PelvisSettingsMove",    "이동"),
    ("PelvisSettingsProne",   "다운"),
]

_LINES: list[str] = []


def log(msg: str = "") -> None:
    _LINES.append(msg)
    unreal.log(msg)


def section(title: str) -> None:
    log("")
    log("=" * 78)
    log(title)
    log("=" * 78)


def load_generated_class() -> Any:
    """AnimBP 생성 클래스를 다양한 경로로 시도."""
    attempts = []

    # 1) unreal.load_class
    try:
        cls = unreal.load_class(None, GEN_CLASS_PATH)
        if cls is not None:
            return cls
        attempts.append(("load_class", "None 반환"))
    except Exception as e:
        attempts.append(("load_class", f"{type(e).__name__}: {e}"))

    # 2) unreal.load_object
    try:
        obj = unreal.load_object(None, GEN_CLASS_PATH)
        if obj is not None:
            return obj
        attempts.append(("load_object", "None 반환"))
    except Exception as e:
        attempts.append(("load_object", f"{type(e).__name__}: {e}"))

    # 3) AnimBP 자체에서 속성으로
    try:
        bp = unreal.load_asset(ASSET_PATH)
        for prop in ("generated_class", "GeneratedClass", "SkeletonGeneratedClass",
                     "skeleton_generated_class", "parent_class"):
            try:
                v = bp.get_editor_property(prop)
                if v is not None:
                    return v
            except Exception:
                continue
        attempts.append(("AnimBP prop scan", "매치 없음"))
    except Exception as e:
        attempts.append(("load_asset", f"{type(e).__name__}: {e}"))

    log("[ERR] generated class 로드 실패. 시도 이력:")
    for method, err in attempts:
        log(f"  · {method}: {err}")
    return None


def dump_struct(label: str, value: Any) -> None:
    log(f"\n[{label}]")
    if value is None:
        log("  (None)")
        return

    # export_text 우선
    try:
        text = value.export_text()
        if text and text != "()":
            for chunk in text.replace("),", ")\n").split("\n"):
                log(f"  {chunk}")
            return
    except Exception:
        pass

    # dir() 기반 프로퍼티 순회
    for name in sorted(dir(value)):
        if name.startswith("_"):
            continue
        try:
            v = value.get_editor_property(name)
        except Exception:
            continue
        if callable(v):
            continue
        log(f"  {name} = {v}")


def main() -> None:
    section(f"에셋: {ASSET_PATH}")

    gen_class = load_generated_class()
    if gen_class is None:
        log("[FAIL] 생성 클래스 접근 불가 — 덤프 중단")
        return

    log(f"  generated class = {gen_class}")
    log(f"  class name = {gen_class.get_name() if hasattr(gen_class, 'get_name') else gen_class}")

    try:
        cdo = unreal.get_default_object(gen_class)
    except Exception as e:
        log(f"[FAIL] CDO 접근 실패: {e}")
        return

    log(f"  CDO = {cdo}")

    section("PelvisSettings 3 프로필 덤프")
    for var_name, label_ko in VARIABLES:
        try:
            value = cdo.get_editor_property(var_name)
        except Exception as e:
            log(f"\n[{var_name} / {label_ko}]")
            log(f"  (err: {type(e).__name__}: {str(e)[:120]})")
            continue
        dump_struct(f"{var_name}  ({label_ko})", value)

    out_dir = unreal.Paths.project_saved_dir() + "Logs"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "PelvisSettingsDump.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(_LINES))
    log("")
    log(f"=> 저장됨: {out_path}")


main()
