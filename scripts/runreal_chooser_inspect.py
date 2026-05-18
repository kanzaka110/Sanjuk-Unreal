"""runreal `editor_run_python` 으로 Chooser ResultsStructs 직접 추출.

Monolith blueprint_query.get_cdo_properties 는 ChooserTable 의 ResultsStructs
InstancedStruct 내용물을 `{}` 빈 직렬화 (protected) 한다 — [[reference-monolith-animgraph-editing-limits]].

runreal MCP 의 `editor_run_python` 은 UE 안에서 Python `unreal` 모듈을 직접 실행하므로
property reflection 으로 protected 우회 가능. 이 스크립트는 두 가지 출력:

1) 호스트 (현재 머신, claude-code) 에서 실행 — runreal MCP 호출용 Python source 를
   생성/검증해서 stdout 으로 print. UE 가동 시 사용자가 이 결과를 복붙하거나
   `mcp__unreal-mcp__editor_run_python` 에 그대로 전달.

2) UE 안 Python 인터프리터에서 실행 — `__name__ == "__main__"` 분기 아님.
   runreal 의 stdin 으로 들어가야 작동.

사용법 (호스트):
    py scripts/runreal_chooser_inspect.py --asset /Game/Art/Character/PC/PC_01/StateMachine/EvieAnimChooser
    → Python source 출력 → mcp__unreal-mcp__editor_run_python(payload=...) 호출

UE 미가동 환경에선 dry-run 으로 source 미리보기만.
"""
from __future__ import annotations

import argparse
import textwrap


def build_python_payload(asset_path: str) -> str:
    """UE 안에서 실행될 Python source. runreal 규칙:
    - 반드시 import unreal 로 시작
    - 주석 금지 (# 또는 ''')
    - print() 만 출력
    - JSON 으로 출력 권장
    """
    # runreal 규칙: 주석 금지. f-string 으로 asset_path 만 주입.
    src = textwrap.dedent(f"""
        import unreal
        import json
        out = {{"asset_path": "{asset_path}"}}
        chooser = unreal.load_asset("{asset_path}")
        if chooser is None:
            out["error"] = "load_asset returned None"
        else:
            out["class"] = chooser.get_class().get_name()
            try:
                results = chooser.get_editor_property("ResultsStructs")
                out["results_structs_type"] = type(results).__name__
                if hasattr(results, "__len__"):
                    out["results_count"] = len(results)
                rows = []
                for i, entry in enumerate(results or []):
                    item = {{"index": i}}
                    if hasattr(entry, "get_editor_property"):
                        try:
                            anim = entry.get_editor_property("AnimationAsset")
                            item["AnimationAsset"] = str(anim.get_path_name()) if anim else None
                        except Exception as e:
                            item["AnimationAsset_error"] = str(e)
                    item["repr"] = str(entry)[:200]
                    rows.append(item)
                out["rows"] = rows[:50]
            except Exception as e:
                out["results_error"] = str(e)
            try:
                cols = chooser.get_editor_property("ColumnsStructs")
                out["columns_count"] = len(cols) if hasattr(cols, "__len__") else None
            except Exception as e:
                out["columns_error"] = str(e)
        print(json.dumps(out, indent=2, ensure_ascii=False))
    """).strip()
    return src


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument(
        "--asset",
        default="/Game/Art/Character/PC/PC_01/StateMachine/EvieAnimChooser",
        help="Chooser asset path (.uasset 없이 /Game/... )",
    )
    ap.add_argument("--write", help="결과 source 를 파일로 저장 (선택)")
    args = ap.parse_args()

    payload = build_python_payload(args.asset)
    print(payload)
    if args.write:
        with open(args.write, "w", encoding="utf-8") as f:
            f.write(payload)
        print(f"\n[written] {args.write}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
