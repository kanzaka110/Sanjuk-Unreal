"""
N_LockOn_Moveing / N_Battle_GroundMoving nested chooser 전용 덤프.

GroundMoving.GroundMoving 아래 inner ChooserTable들을 재귀 탐색하고
컬럼 export_text + RowValues + ResultsStructs(가능 시) 풀텍스트로 저장.

실행:
  UE Editor > Python Console
  py "C:/Dev/Sanjuk-Unreal/scripts/dump_lockon_chooser.py"

출력: Saved/Logs/LockOnChooserDump.txt
"""
from __future__ import annotations

import logging
import os
from typing import Any

import unreal

logger = logging.getLogger(__name__)

ROOT_PATH = "/Game/Art/Character/PC/PC_01/StateMachine/GroundMoving.GroundMoving"
OUT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(), "Logs", "LockOnChooserDump.txt"
)

LINES: list[str] = []


def log(msg: str = "") -> None:
    LINES.append(msg)
    unreal.log(msg)


def safe_export(obj: Any) -> str:
    try:
        if hasattr(obj, "export_text"):
            return obj.export_text()
    except Exception as exc:  # noqa: BLE001
        return f"<export err: {exc}>"
    return repr(obj)


def dump_table(ct: unreal.Object, label: str, depth: int = 0) -> None:
    indent = "  " * depth
    log("")
    log(f"{indent}{'=' * 90}")
    log(f"{indent}[{label}] path={ct.get_path_name()}")
    log(f"{indent}{'=' * 90}")

    cols: list[Any] = []
    results: list[Any] = []
    disabled: list[bool] = []
    nested_objs: list[Any] = []
    try:
        cols = list(ct.get_editor_property("ColumnsStructs") or [])
    except Exception as exc:  # noqa: BLE001
        log(f"{indent}  cols err: {exc}")
    try:
        results = list(ct.get_editor_property("ResultsStructs") or [])
    except Exception as exc:  # noqa: BLE001
        log(f"{indent}  results err (protected?): {exc}")
    try:
        disabled = list(ct.get_editor_property("DisabledRows") or [])
    except Exception:  # noqa: BLE001
        pass
    try:
        nested_objs = list(ct.get_editor_property("NestedObjects") or [])
    except Exception:  # noqa: BLE001
        pass

    log(f"{indent}  rows={len(results)} cols={len(cols)} nested_objs={len(nested_objs)}")
    log(f"{indent}  disabled={disabled}")

    log(f"{indent}  --- Columns (full export) ---")
    for ci, col in enumerate(cols):
        log(f"{indent}  col[{ci}]:")
        text = safe_export(col)
        for line in text.splitlines():
            log(f"{indent}    {line}")

    log(f"{indent}  --- Results (full export) ---")
    for ri, res in enumerate(results):
        flag = " (DISABLED)" if ri < len(disabled) and disabled[ri] else ""
        text = safe_export(res)
        first = text.splitlines()[0] if text else ""
        log(f"{indent}  row[{ri}]{flag}: {first[:200]}")
        if len(text.splitlines()) > 1:
            for line in text.splitlines()[1:]:
                log(f"{indent}    {line[:300]}")

    # NestedObjects 안에 자식 ChooserTable이 있는 경우 재귀
    for child in nested_objs:
        if isinstance(child, unreal.ChooserTable):
            dump_table(child, child.get_name(), depth + 1)
        else:
            log(f"{indent}  nested_obj type={type(child).__name__} -> {child}")


def main() -> None:
    root = unreal.load_object(None, ROOT_PATH)
    if root is None:
        log(f"load failed: {ROOT_PATH}")
        return
    dump_table(root, "GroundMoving (ROOT)")

    # 직접 inner 경로도 시도 (NestedObjects가 비어있을 경우 fallback)
    for sub in [
        "N_Battle_GroundMoving",
        "N_Battle_GroundMoving.N_LockOn_Moveing",
        "N_Peaceful_GroundMoving",
    ]:
        full = f"{ROOT_PATH}:{sub}"
        obj = unreal.load_object(None, full)
        if obj is None:
            log(f"  (could not load {full})")
            continue
        if any(obj.get_path_name() == ct_path for ct_path in []):
            continue
        dump_table(obj, sub)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(LINES))
    log(f"\nWrote: {OUT_PATH}")


main()
