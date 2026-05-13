"""
Chooser ResultsStructs의 Tags(GameplayTagColumn) 컬럼 현재 라벨링 상태를 덤프.

대상:
  /Game/Art/Character/PC/PC_01/StateMachine/EvieAnimChooser_StateMachine
  + 5개 sub-chooser:
    GroundIdle, GroundMoving, Falling, Montage, SplineMoving
  + GroundMoving 내부 nested chooser (N_Battle_*, N_Peaceful_*, ...) 재귀

목적:
  - Start / Pivot / Stop / Loop 시리즈 row의 Tags 필드 현재 값 확인
  - 라벨링이 이미 완성됐는지, 부분/없음인지 판정
  - Task 2(라벨링) skip 가능 여부 결정 + Task 3 (IsStarting 그래프) 진입 판정

실행:
  UE 에디터 > Window > Developer Tools > Python Console
  py "C:/Dev/Sanjuk-Unreal/scripts/dump_chooser_tags.py"

출력:
  Saved/Logs/ChooserTagsDump.txt
"""
from __future__ import annotations

import os
from typing import Any, Optional

import unreal


ROOT = (
    "/Game/Art/Character/PC/PC_01/StateMachine/"
    "EvieAnimChooser_StateMachine.EvieAnimChooser_StateMachine"
)

# StateMachine 외에 EvieAnimChooser_StateMachine asset에 nested된 sub-chooser는
# NestedChoosers를 통해 자동 traverse. 추가로 분리된 asset인 GroundIdle/GroundMoving/
# Falling 도 ROOT에서 ObjectChooser ref로 가리키므로 별도 큐로 추가.
EXTRA_ROOTS = [
    "/Game/Art/Character/PC/PC_01/StateMachine/GroundIdle.GroundIdle",
    "/Game/Art/Character/PC/PC_01/StateMachine/GroundMoving.GroundMoving",
    "/Game/Art/Character/PC/PC_01/StateMachine/Falling.Falling",
]

OUT_PATH = os.path.join(
    unreal.Paths.project_saved_dir(), "Logs", "ChooserTagsDump.txt"
)

LINES: list[str] = []


def log(msg: str = "") -> None:
    LINES.append(msg)
    # print는 hooks 룰 위반이지만 UE Output Log 출력 용도이므로 의도적 유지
    print(msg)  # noqa: T201


def safe_export(s: Any) -> str:
    try:
        if hasattr(s, "export_text"):
            return s.export_text()
    except Exception as e:  # noqa: BLE001
        return f"<export error: {e}>"
    try:
        return repr(s)
    except Exception as e:  # noqa: BLE001
        return f"<repr error: {e}>"


def struct_name(inst: Any) -> str:
    try:
        if hasattr(inst, "get_struct"):
            ss = inst.get_struct()
            if ss is not None:
                return ss.get_name()
    except Exception:  # noqa: BLE001
        pass
    return type(inst).__name__


def get_row_values_from_column(col_export: str) -> Optional[str]:
    """Column export_text에서 RowValues=(...) 부분만 추출."""
    idx = col_export.find("RowValues=")
    if idx < 0:
        return None
    # 단순 brace 카운트로 끝 찾기
    start = col_export.find("(", idx)
    if start < 0:
        return None
    depth = 0
    for i in range(start, len(col_export)):
        c = col_export[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return col_export[idx : i + 1]
    return None


def classify_row_label(row_first_line: str) -> str:
    """row의 첫 줄에서 시퀀스 이름 패턴으로 Start/Pivot/Stop/Loop 분류."""
    s = row_first_line
    # 패턴 매칭: P_Player_*_Run_Start_*, _Turn_*_(090|180), _Stop_, _Loop_ 등
    low = s.lower()
    if "_start_" in low or "start_" in low and "loop" not in low:
        return "Start"
    if (
        "_turn_" in low
        and ("_090" in low or "_180" in low)
    ) or "_pivot_" in low:
        return "Pivot"
    if "_stop_" in low:
        return "Stop"
    if "_loop_" in low or "loop_" in low:
        return "Loop"
    if "_idle_" in low or "idle" in low:
        return "Idle"
    if "_jump_" in low or "_fall_" in low or "_land_" in low:
        return "Air"
    return "Other"


def dump_chooser(obj_path: str, label: str, depth: int = 0) -> list[str]:
    indent = "  " * depth
    log("")
    log(f"{indent}{'=' * 88}")
    log(f"{indent}[{label}] {obj_path}")
    log(f"{indent}{'=' * 88}")

    ct = unreal.load_object(None, obj_path)
    if ct is None:
        log(f"{indent}  ! load failed")
        return []

    try:
        results = list(ct.get_editor_property("ResultsStructs") or [])
    except Exception as e:  # noqa: BLE001
        log(f"{indent}  results err: {e}")
        results = []
    try:
        columns = list(ct.get_editor_property("ColumnsStructs") or [])
    except Exception as e:  # noqa: BLE001
        log(f"{indent}  columns err: {e}")
        columns = []
    try:
        disabled = list(ct.get_editor_property("DisabledRows") or [])
    except Exception:  # noqa: BLE001
        disabled = []
    try:
        nested = list(ct.get_editor_property("NestedChoosers") or [])
    except Exception:  # noqa: BLE001
        nested = []

    log(f"{indent}  rows={len(results)}  cols={len(columns)}  disabled_idx={[i for i,d in enumerate(disabled) if d]}")

    # ---- Columns: 타입과 RowValues 요약 ----
    tag_columns: list[int] = []
    log(f"{indent}  --- Columns ---")
    for ci, col in enumerate(columns):
        tname = struct_name(col)
        log(f"{indent}  col[{ci}] type={tname}")
        text = safe_export(col)
        rv = get_row_values_from_column(text)
        if rv is not None:
            # 길면 잘라서
            short = rv if len(rv) <= 1200 else rv[:1200] + "...(truncated)"
            log(f"{indent}    RowValues={short}")
        else:
            # InputValue/Binding 부분만 한 줄
            first = text.splitlines()[0] if text else ""
            log(f"{indent}    text[:200]={first[:200]}")
        # Tag 관련 컬럼 식별 (이름에 Tag 포함)
        if "Tag" in tname or "Gameplay" in tname:
            tag_columns.append(ci)

    if tag_columns:
        log(f"{indent}  >>> Tag-like columns at indices: {tag_columns}")
    else:
        log(f"{indent}  >>> NO Tag-like column found in this chooser")

    # ---- Results: 시퀀스명 + Tags 컬럼 값 ----
    log(f"{indent}  --- Results (row idx | classify | seq | tags) ---")
    counters: dict[str, int] = {}
    tag_status: dict[str, dict[str, int]] = {}  # category -> {tagged:n, empty:n}
    for ri, res in enumerate(results):
        rtype = struct_name(res)
        rtext = safe_export(res)
        first = rtext.splitlines()[0] if rtext else ""
        cat = classify_row_label(first)
        counters[cat] = counters.get(cat, 0) + 1

        # Tag 컬럼들의 row 값
        tag_summary_parts: list[str] = []
        any_tagged = False
        for ci in tag_columns:
            col = columns[ci]
            ctext = safe_export(col)
            # RowValues가 array면 ri번째 추출 시도
            # 간단히 정규식 대신: RowValues=( (Tags=...), (Tags=...), ... )
            rv = get_row_values_from_column(ctext)
            if not rv:
                tag_summary_parts.append(f"col{ci}:?")
                continue
            # split row-level parens
            row_vals = _split_rowvalues_top(rv)
            if 0 <= ri < len(row_vals):
                v = row_vals[ri]
                tag_summary_parts.append(f"col{ci}:{v}")
                if v not in ("()", "", "(Tags=())", "(GameplayTags=())"):
                    any_tagged = True
            else:
                tag_summary_parts.append(f"col{ci}:<no row {ri}>")

        # 카테고리별 tagged 카운트
        cat_st = tag_status.setdefault(cat, {"tagged": 0, "empty": 0})
        if any_tagged:
            cat_st["tagged"] += 1
        else:
            cat_st["empty"] += 1

        flag = " (DISABLED)" if ri < len(disabled) and disabled[ri] else ""
        log(
            f"{indent}  row[{ri:>3}] {cat:<6} {rtype:<28}{flag}  "
            f"seq={first[:120]}  tags={'; '.join(tag_summary_parts)[:200]}"
        )

    log(f"{indent}  --- Category counts: {counters} ---")
    log(f"{indent}  --- Tag status by category: {tag_status} ---")

    return [str(n) for n in nested]


def _split_rowvalues_top(rv_text: str) -> list[str]:
    """RowValues=( (val0), (val1), ... ) 에서 top-level row 항목만 list로.

    가장 바깥쪽 괄호 안에서 depth=1인 ( ) 단위로 split.
    """
    # 바깥 괄호 제거
    s = rv_text
    eq = s.find("=")
    if eq < 0:
        return []
    s = s[eq + 1 :].strip()
    if not (s.startswith("(") and s.endswith(")")):
        return []
    inner = s[1:-1]
    out: list[str] = []
    depth = 0
    start = 0
    i = 0
    while i < len(inner):
        c = inner[i]
        if c == "(":
            if depth == 0:
                start = i
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                out.append(inner[start : i + 1])
        elif c == "," and depth == 0:
            # 빈 슬롯
            pass
        i += 1
    return out


def main() -> None:
    queue: list[tuple[str, str]] = [(ROOT, "ROOT")]
    for p in EXTRA_ROOTS:
        queue.append((p, p.rsplit("/", 1)[-1].split(".")[-1]))

    visited: set[str] = set()
    while queue:
        path, label = queue.pop(0)
        if path in visited:
            continue
        visited.add(path)
        children = dump_chooser(path, label)
        for c in children:
            if c and c not in visited:
                seg = c.split(":")[-1] if ":" in c else c.split(".")[-1]
                queue.append((c, seg))

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(LINES))
    log("")
    log(f"Wrote: {OUT_PATH}")


main()
