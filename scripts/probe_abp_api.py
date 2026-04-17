"""Diagnose what UE Python API exposes for AnimBlueprint graph access.

Run inside Unreal Editor:
    exec(open("C:/Dev/Sanjuk-Unreal/scripts/probe_abp_api.py").read())
"""
from __future__ import annotations

import unreal

ABP_PATH: str = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"


def line(t: str = "") -> None:
    print(t)


def section(t: str) -> None:
    line("\n" + "=" * 70)
    line(t)
    line("=" * 70)


def main() -> None:
    abp = unreal.load_asset(ABP_PATH)
    if not abp:
        line("[ERROR] Failed to load " + ABP_PATH)
        return

    line(f"[asset] {abp.get_name()}  class={abp.get_class().get_name()}")

    section("1) dir(abp) — 'graph' 포함 속성")
    names = [n for n in dir(abp) if "graph" in n.lower()]
    for n in names:
        line("  " + n)

    section("2) get_editor_property 후보들")
    for prop in [
        "ubergraph_pages", "UbergraphPages",
        "function_graphs", "FunctionGraphs",
        "macro_graphs", "delegate_graphs", "intermediate_graphs",
        "anim_graph", "animation_graph", "AnimationGraphs",
        "simple_construction_script",
    ]:
        try:
            val = abp.get_editor_property(prop)
            if val is None:
                continue
            n = len(val) if hasattr(val, "__len__") else "(scalar)"
            line(f"  {prop} -> {n}   type={type(val).__name__}")
        except Exception as e:
            line(f"  {prop} !! {type(e).__name__}: {str(e)[:80]}")

    section("3) 속성 직접 접근 (attribute)")
    for attr in ["function_graphs", "ubergraph_pages", "macro_graphs"]:
        try:
            val = getattr(abp, attr, None)
            if val is None:
                line(f"  {attr} = None")
                continue
            n = len(val) if hasattr(val, "__len__") else "(scalar)"
            line(f"  {attr} -> {n}")
        except Exception as e:
            line(f"  {attr} !! {type(e).__name__}")

    section("4) BlueprintEditorLibrary API")
    bel = unreal.BlueprintEditorLibrary
    for m in dir(bel):
        if m.startswith("_"):
            continue
        if any(k in m.lower() for k in ("graph", "node", "anim")):
            line("  " + m)

    section("5) unreal.* 모듈 중 AnimGraph 관련")
    for n in dir(unreal):
        if "animgraph" in n.lower() or "animblueprint" in n.lower():
            line("  " + n)

    section("6) generated_class의 anim_node_properties")
    try:
        gen = abp.get_editor_property("generated_class")
        line(f"  generated_class = {gen}")
        if gen:
            try:
                props = gen.get_editor_property("anim_node_properties")
                line(f"  anim_node_properties count = "
                     f"{len(props) if props else 0}")
            except Exception as e:
                line(f"  anim_node_properties !! {type(e).__name__}: "
                     f"{str(e)[:100]}")
            for pn in dir(gen):
                if any(k in pn.lower() for k in
                       ("anim_node", "graph", "linked")):
                    line("  gen." + pn)
    except Exception as e:
        line(f"  generated_class err: {e}")


main()
