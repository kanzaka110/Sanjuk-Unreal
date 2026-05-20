"""GroundMoving Chooser 의 columns 에서 CircleStrafeHysteresis 컬럼 위치를 dump.

이 스크립트는 UE 안 Python interpreter 에서 실행되어야 한다 (runreal MCP 또는 에디터 Output Log).
호스트 실행 시엔 payload Python source 를 stdout 으로 출력.
"""
from __future__ import annotations

import textwrap


def build_payload(asset_path: str) -> str:
    src = textwrap.dedent(f"""
        import unreal
        import json
        out = {{"asset_path": "{asset_path}"}}
        chooser = unreal.load_asset("{asset_path}")
        if chooser is None:
            out["error"] = "load_asset None"
        else:
            try:
                cols = chooser.get_editor_property("ColumnsStructs")
                col_info = []
                for i, c in enumerate(cols or []):
                    item = {{"idx": i}}
                    try:
                        item["repr"] = str(c)[:300]
                        item["type"] = type(c).__name__
                        try:
                            inner = c.get_editor_property("InputValue")
                            item["input_value_repr"] = str(inner)[:200]
                            try:
                                bv = inner.get_editor_property("Binding") if hasattr(inner, "get_editor_property") else None
                                if bv:
                                    item["binding_repr"] = str(bv)[:200]
                            except Exception:
                                pass
                        except Exception:
                            pass
                    except Exception as e:
                        item["err"] = str(e)
                    col_info.append(item)
                out["columns"] = col_info
                out["columns_count"] = len(col_info)
            except Exception as e:
                out["columns_error"] = str(e)
            try:
                rs = chooser.get_editor_property("ResultsStructs")
                out["rows_count"] = len(rs) if hasattr(rs, "__len__") else None
            except Exception as e:
                out["rows_error"] = str(e)
        print(json.dumps(out, indent=2, ensure_ascii=False))
    """).strip()
    return src


if __name__ == "__main__":
    print(build_payload("/Game/Art/Character/PC/PC_01/StateMachine/GroundMoving"))
