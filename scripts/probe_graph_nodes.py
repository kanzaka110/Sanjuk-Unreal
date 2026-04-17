"""2차 진단: EdGraph의 노드에 접근하는 경로를 찾는다.

Run inside Unreal Editor:
    exec(open("C:/Dev/Sanjuk-Unreal/scripts/probe_graph_nodes.py").read())
"""
from __future__ import annotations

import unreal

ABP_PATH: str = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"


def section(t: str) -> None:
    print("\n" + "=" * 70)
    print(t)
    print("=" * 70)


def main() -> None:
    abp = unreal.load_asset(ABP_PATH)
    if not abp:
        print("[ERROR] load fail")
        return

    graphs = list(abp.get_animation_graphs())
    if not graphs:
        print("no graphs")
        return

    g = graphs[0]
    print(f"[graph] {g.get_name()}  class={g.get_class().get_name()}")

    section("A) dir(graph)  (non-dunder)")
    for n in dir(g):
        if not n.startswith("_"):
            print("  " + n)

    section("B) get_editor_property 다양한 이름")
    for p in ["nodes", "Nodes", "sub_graphs", "SubGraphs",
              "schema", "graph_guid", "GraphGuid"]:
        try:
            v = g.get_editor_property(p)
            nn = len(v) if hasattr(v, "__len__") else "(scalar)"
            print(f"  {p} -> {nn}  type={type(v).__name__}")
        except Exception as e:
            print(f"  {p} !! {type(e).__name__}: {str(e)[:80]}")

    section("C) unreal.AnimGraphLibrary API")
    try:
        agl = unreal.AnimGraphLibrary
        for n in dir(agl):
            if not n.startswith("_"):
                print("  " + n)
    except Exception as e:
        print("  none:", e)

    section("D) 패키지 내 inner object — EdGraphNode 검색")
    pkg_path = abp.get_path_name().split(".")[0]
    print("  package path:", pkg_path)
    try:
        eal = unreal.EditorAssetLibrary
        # find all assets in the package
        assets = eal.list_assets(pkg_path, recursive=False,
                                 include_folder=False)
        print(f"  list_assets -> {len(assets)} items")
        for a in assets[:10]:
            print("   ·", a)
    except Exception as e:
        print("  list_assets err:", e)

    section("E) SystemLibrary / get_object_name of outer chain")
    try:
        outer = abp.get_outer()
        print("  outer =", outer, " name=",
              outer.get_name() if outer else None)
    except Exception as e:
        print("  err:", e)

    section("F) find_graph via BlueprintEditorLibrary")
    try:
        bel = unreal.BlueprintEditorLibrary
        found = bel.find_graph(abp, "AnimGraph")
        if found:
            print(f"  find_graph('AnimGraph') -> {found.get_name()}")
            for p in ["nodes", "Nodes"]:
                try:
                    v = found.get_editor_property(p)
                    nn = len(v) if hasattr(v, "__len__") else 0
                    print(f"    {p} -> {nn}")
                except Exception as e:
                    print(f"    {p} !! {type(e).__name__}")
        else:
            print("  find_graph -> None")
    except Exception as e:
        print("  err:", e)

    section("G) AnimBlueprint 속성 전체 스캔 (len > 0인 것만)")
    for n in dir(abp):
        if n.startswith("_"):
            continue
        try:
            v = abp.get_editor_property(n)
            if hasattr(v, "__len__") and len(v) > 0:
                print(f"  {n} -> {len(v)}  type={type(v).__name__}")
        except Exception:
            continue


main()
