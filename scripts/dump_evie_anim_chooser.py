"""
EvieAnimChooser_StateMachine 의 모든 sub-chooser 의 ColumnsStructs / ResultsStructs / DisabledRows
를 export_text 로 덤프한다.

목적: GroundIdle 분기 sub-chooser 의 정확한 컬럼 바인딩 (Prev* 변수) 식별 및
GroundMoving 분기와 비교해 어느 컬럼이 Falling→GroundIdle 1틱 mismatch 의 원인인지 특정.

실행: UE 에디터 Output Log 또는 Window > Developer Tools > Python Console
  py "C:/Dev/Sanjuk-Unreal/scripts/dump_evie_anim_chooser.py"

결과는 Saved/Logs/EvieAnimChooserDump.txt 로 저장.
"""
from __future__ import annotations

import os
from typing import Any

import unreal

ROOT = (
    "/Game/Art/Character/PC/PC_01/StateMachine/"
    "EvieAnimChooser_StateMachine.EvieAnimChooser_StateMachine"
)

OUT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(), "Logs", "EvieAnimChooserDump.txt"
)

lines: list[str] = []


def log(s: str = "") -> None:
    lines.append(s)
    print(s)


def export_struct(s: Any) -> str:
    """FInstancedStruct -> 사람이 읽을 수 있는 텍스트."""
    try:
        if hasattr(s, "export_text"):
            return s.export_text()
    except Exception as e:
        return f"<export_text error: {e}>"
    try:
        return repr(s)
    except Exception as e:
        return f"<repr error: {e}>"


def dump_chooser(obj_path: str, label: str) -> list[str]:
    """주어진 ChooserTable 의 컬럼/결과 dump. 자식 NestedChoosers 경로 list 반환."""
    log("")
    log("=" * 90)
    log(f"[{label}] {obj_path}")
    log("=" * 90)

    ct = unreal.load_object(None, obj_path)
    if ct is None:
        log("  ! load failed")
        return []

    try:
        results = list(ct.get_editor_property("ResultsStructs") or [])
    except Exception as e:
        log(f"  results err: {e}")
        results = []
    try:
        columns = list(ct.get_editor_property("ColumnsStructs") or [])
    except Exception as e:
        log(f"  columns err: {e}")
        columns = []
    try:
        disabled = list(ct.get_editor_property("DisabledRows") or [])
    except Exception:
        disabled = []
    try:
        nested = list(ct.get_editor_property("NestedChoosers") or [])
    except Exception:
        nested = []

    log(f"  rows={len(results)}  cols={len(columns)}  disabled={list(disabled)}")
    log(f"  nested={[str(n) for n in nested]}")

    # Columns
    log("  --- Columns ---")
    for ci, col in enumerate(columns):
        try:
            ss = col.get_struct() if hasattr(col, "get_struct") else None
            type_name = ss.get_name() if ss else type(col).__name__
        except Exception:
            type_name = "?"
        log(f"  col[{ci}] type={type_name}")
        text = export_struct(col)
        for line in text.splitlines()[:80]:
            log(f"      {line}")

    # Results
    log("  --- Results ---")
    for ri, res in enumerate(results):
        try:
            ss = res.get_struct() if hasattr(res, "get_struct") else None
            type_name = ss.get_name() if ss else type(res).__name__
        except Exception:
            type_name = "?"
        text = export_struct(res)
        first_line = text.splitlines()[0] if text else ""
        flag = " (DISABLED)" if ri < len(disabled) and disabled[ri] else ""
        log(f"  row[{ri}] type={type_name}{flag}  {first_line[:240]}")

    # nested 경로 list 반환 (자식 chooser 재귀용)
    return [str(n) for n in nested]


def main() -> None:
    queue: list[tuple[str, str]] = [(ROOT, "ROOT")]
    visited: set[str] = set()
    while queue:
        path, label = queue.pop(0)
        if path in visited:
            continue
        visited.add(path)
        children = dump_chooser(path, label)
        for c in children:
            if c and c not in visited:
                # subobject path 라면 라벨은 마지막 세그먼트
                seg = c.split(":")[-1] if ":" in c else c.split(".")[-1]
                queue.append((c, seg))

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\nWrote: {OUT_PATH}")


main()
