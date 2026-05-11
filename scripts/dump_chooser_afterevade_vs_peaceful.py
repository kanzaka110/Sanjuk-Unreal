"""
@Description: PC_01 GroundMoving Chooser의 N_AfterEvade vs N_TransitToGroundMoving_Peaceful
              두 sub-chooser의 ColumnsStructs/ResultsStructs를 dump하고
              Pivot/StartAfterEvade 패턴 매칭을 요약. Monolith scripting_query.execute_script로 실행.
"""
import unreal
import json
import os
import re
import time

ROOT = "/Game/Art/Character/PC/PC_01/StateMachine/GroundMoving.GroundMoving"
TARGETS = [
    ":N_AfterEvade",
    ":N_TransitToGroundMoving_Peaceful",
    "",  # root도 같이 떠서 row 우선순위 확인
]

OUT_DIR = r"C:\Dev\Sanjuk-Unreal\dumps"
os.makedirs(OUT_DIR, exist_ok=True)
ts = time.strftime("%Y%m%d_%H%M%S")
out_path = os.path.join(OUT_DIR, f"chooser_afterevade_vs_peaceful_{ts}.txt")


def safe_export(s):
    try:
        return s.export_text() if hasattr(s, "export_text") else repr(s)
    except Exception as e:
        return f"<export_error: {e}>"


def struct_type(s):
    try:
        ss = s.get_struct() if hasattr(s, "get_struct") else None
        return ss.get_name() if ss else type(s).__name__
    except Exception:
        return "UnknownInstancedStruct"


def dump_chooser(obj_path, fh):
    fh.write(f"\n=========== {obj_path} ===========\n")
    ct = unreal.load_object(None, obj_path)
    if ct is None:
        fh.write("  FAILED to load\n")
        return {"path": obj_path, "loaded": False}

    try:
        results = ct.get_editor_property("ResultsStructs") or []
    except Exception as e:
        fh.write(f"  get ResultsStructs error: {e}\n")
        results = []
    try:
        columns = ct.get_editor_property("ColumnsStructs") or []
    except Exception as e:
        fh.write(f"  get ColumnsStructs error: {e}\n")
        columns = []
    try:
        disabled = list(ct.get_editor_property("DisabledRows") or [])
    except Exception:
        disabled = []

    fh.write(f"  rows={len(results)} cols={len(columns)} disabled={disabled}\n")

    fh.write("  --- Columns (조건) ---\n")
    col_summaries = []
    for ci, col in enumerate(columns):
        t = struct_type(col)
        exp = safe_export(col)
        col_summaries.append({"index": ci, "type": t, "first": exp.splitlines()[0] if exp else ""})
        fh.write(f"  col[{ci}] type={t}\n")
        for line in exp.splitlines()[:50]:
            fh.write(f"      {line}\n")

    fh.write("  --- Results (출력) ---\n")
    row_summaries = []
    for ri, res in enumerate(results):
        t = struct_type(res)
        exp = safe_export(res)
        first = exp.splitlines()[0] if exp else ""
        # AnimSequence asset path 추출
        m = re.findall(r"/Game/[^'\"\s,)\]]+", exp)
        row_summaries.append({"index": ri, "type": t, "anim_paths": m[:8]})
        fh.write(f"  row[{ri}] type={t}  {first[:240]}\n")
        for path in m[:8]:
            fh.write(f"      anim: {path}\n")

    return {
        "path": obj_path,
        "loaded": True,
        "rows": len(results),
        "cols": len(columns),
        "disabled": disabled,
        "col_summaries": col_summaries,
        "row_summaries": row_summaries,
    }


summaries = []
with open(out_path, "w", encoding="utf-8") as fh:
    fh.write(f"# PC_01 GroundMoving Chooser sub-dump @ {ts}\n")
    for suf in TARGETS:
        path = ROOT + suf
        try:
            s = dump_chooser(path, fh)
            summaries.append(s)
        except Exception as e:
            fh.write(f"[ERROR] {suf}: {e}\n")
            summaries.append({"path": path, "error": str(e)})

    # 요약: Pivot/StartAfterEvade 패턴 매칭
    fh.write("\n=== 요약: Pivot / StartAfterEvade 패턴 분포 ===\n")
    for s in summaries:
        if not s.get("loaded"):
            continue
        pivot_rows = []
        evade_rows = []
        for r in s["row_summaries"]:
            for p in r.get("anim_paths", []):
                if "Pivot" in p:
                    pivot_rows.append((r["index"], p))
                if "StartAfterEvade" in p:
                    evade_rows.append((r["index"], p))
        fh.write(f"\n[{s['path']}]\n")
        fh.write(f"  Pivot rows: {len(pivot_rows)}\n")
        for ri, p in pivot_rows:
            fh.write(f"    row[{ri}] {p}\n")
        fh.write(f"  StartAfterEvade rows: {len(evade_rows)}\n")
        for ri, p in evade_rows:
            fh.write(f"    row[{ri}] {p}\n")

print(f"DONE: {out_path}")
print(json.dumps([{"path": s.get("path"), "rows": s.get("rows"), "cols": s.get("cols")} for s in summaries], ensure_ascii=False, indent=2))
