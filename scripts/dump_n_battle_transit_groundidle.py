"""GroundIdle 의 nested chooser N_Battle_TransitToGroundIdle 전체 구조 dump.

P_Player_Fist_Battle_Jog_Stop_* 4 row 가 어떤 column 의 어떤 MoveSide enum 값과
매핑되는지 확정하기 위한 dump 페이로드 생성기.

Monolith blueprint_query.get_cdo_properties 는 ChooserTable 의 ColumnsStructs /
ResultsStructs InstancedStruct 를 `{}` 빈 직렬화 (protected) — [[reference-monolith-animgraph-editing-limits]].
runreal MCP `editor_run_python` 또는 UE Output Log Python 콘솔로만 우회 가능.

사용 (호스트):
    py scripts/dump_n_battle_transit_groundidle.py
    py scripts/dump_n_battle_transit_groundidle.py --write scripts/_payload.py

  → 생성된 source 를 둘 중 하나로 실행:
    (a) mcp__unreal-mcp__editor_run_python(payload=...)
    (b) UE Editor > Window > Developer Tools > Output Log > Cmd dropdown=Python > 붙여넣기
"""

from __future__ import annotations

import argparse
import textwrap

DEFAULT_PARENT = "/Game/Art/Character/PC/PC_01/StateMachine/GroundIdle.GroundIdle"
DEFAULT_NESTED = "N_Battle_TransitToGroundIdle"


def build_payload(parent_path: str, nested_name: str) -> str:
    """UE 안에서 실행될 Python source. 주석/docstring 금지 (runreal payload 규칙)."""
    nested_full = f"{parent_path}:{nested_name}"
    src = textwrap.dedent(
        f"""
        import unreal
        import json
        PARENT = "{parent_path}"
        NESTED_PATH = "{nested_full}"
        out = {{"parent": PARENT, "nested_path": NESTED_PATH}}
        COL_PROPS = ["InputValue", "DefaultValue", "DefaultRowValue", "RowValues", "FallbackValue", "Comparison", "Enum", "Binding", "InputType"]
        RES_PROPS = ["AnimationAsset", "Asset", "Chooser", "PoseSearchDatabase", "Value"]
        def dump_chooser(obj, label):
            info = {{"label": label, "class": obj.get_class().get_name(), "path": obj.get_path_name()}}
            try:
                cols = obj.get_editor_property("ColumnsStructs")
                info["columns_count"] = len(cols) if cols else 0
                info["columns"] = []
                for i, col in enumerate(cols or []):
                    citem = {{"index": i, "py_type": type(col).__name__, "repr": str(col)[:400]}}
                    if hasattr(col, "get_editor_property"):
                        for pn in COL_PROPS:
                            try:
                                v = col.get_editor_property(pn)
                                citem[pn] = str(v)[:300] if v is not None else None
                            except Exception:
                                pass
                    try:
                        citem["dir"] = [p for p in dir(col) if not p.startswith("_")][:40]
                    except Exception:
                        pass
                    info["columns"].append(citem)
            except Exception as e:
                info["columns_error"] = str(e)
            try:
                results = obj.get_editor_property("ResultsStructs")
                info["results_count"] = len(results) if results else 0
                info["results"] = []
                for i, r in enumerate(results or []):
                    ritem = {{"index": i, "py_type": type(r).__name__, "repr": str(r)[:400]}}
                    if hasattr(r, "get_editor_property"):
                        for pn in RES_PROPS:
                            try:
                                v = r.get_editor_property(pn)
                                if v is None:
                                    ritem[pn] = None
                                elif hasattr(v, "get_path_name"):
                                    ritem[pn] = v.get_path_name()
                                else:
                                    ritem[pn] = str(v)[:300]
                            except Exception:
                                pass
                    info["results"].append(ritem)
            except Exception as e:
                info["results_error"] = str(e)
            try:
                disabled = obj.get_editor_property("DisabledRows")
                info["disabled"] = list(disabled) if disabled else []
            except Exception as e:
                info["disabled_error"] = str(e)
            try:
                output_struct = obj.get_editor_property("OutputStructType")
                info["output_struct_type"] = str(output_struct) if output_struct else None
            except Exception:
                pass
            try:
                ctx = obj.get_editor_property("ContextObjectType")
                info["context_object_type"] = str(ctx) if ctx else None
            except Exception:
                pass
            return info
        parent_obj = unreal.load_asset(PARENT)
        if parent_obj is None:
            out["error"] = "parent load_asset returned None"
        else:
            out["parent_dump"] = dump_chooser(parent_obj, "parent")
            nested_obj = None
            try:
                nested_obj = unreal.load_object(None, NESTED_PATH)
            except Exception as e:
                out["load_object_error"] = str(e)
            if nested_obj is None:
                try:
                    package = parent_obj.get_outer()
                    found = unreal.find_object(package, "{nested_name}")
                    if found:
                        nested_obj = found
                        out["nested_found_via"] = "find_object_in_package"
                except Exception as e:
                    out["find_object_error"] = str(e)
            if nested_obj is None:
                try:
                    cands = []
                    for r in (parent_obj.get_editor_property("ResultsStructs") or []):
                        for pn in ["Chooser", "Asset", "Value"]:
                            try:
                                v = r.get_editor_property(pn)
                                if v and hasattr(v, "get_path_name") and "{nested_name}" in v.get_path_name():
                                    cands.append(v)
                            except Exception:
                                pass
                    if cands:
                        nested_obj = cands[0]
                        out["nested_found_via"] = "results_struct_scan"
                        out["nested_candidates"] = [c.get_path_name() for c in cands]
                except Exception as e:
                    out["scan_error"] = str(e)
            if nested_obj is None:
                out["nested_error"] = "could not resolve nested chooser via any method"
            else:
                out["nested_dump"] = dump_chooser(nested_obj, "nested")
        print(json.dumps(out, indent=2, ensure_ascii=False, default=str)[:60000])
        """
    ).strip()
    return src


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--parent", default=DEFAULT_PARENT, help="parent ChooserTable asset path")
    ap.add_argument("--nested", default=DEFAULT_NESTED, help="nested sub-object name")
    ap.add_argument("--write", help="payload source 저장 경로")
    args = ap.parse_args()

    payload = build_payload(args.parent, args.nested)
    print(payload)
    if args.write:
        with open(args.write, "w", encoding="utf-8") as f:
            f.write(payload)
        print(f"\n[written] {args.write}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
