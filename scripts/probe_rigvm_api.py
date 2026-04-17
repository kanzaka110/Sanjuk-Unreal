"""Probe RigVMController / RigVMGraph API for link enumeration.

Run inside Unreal Editor:
    exec(open("C:/Dev/Sanjuk-Unreal/scripts/probe_rigvm_api.py").read())
"""
from __future__ import annotations

import unreal

CR_PATH: str = "/Game/ART/Character/PC/PC_01/Rig/PC_01_CtrlRig_FootClamp"


def section(t: str) -> None:
    print("\n" + "=" * 70)
    print(t)
    print("=" * 70)


def get_controller(bp):
    for getter in ("get_default_model", "get_focused_model", "get_model"):
        try:
            fn = getattr(bp, getter, None)
            if callable(fn):
                m = fn()
                if m:
                    ctrl = bp.get_or_create_controller(m)
                    if ctrl:
                        return ctrl
        except Exception:
            continue
    try:
        for m in bp.get_all_models():
            ctrl = bp.get_or_create_controller(m)
            if ctrl:
                return ctrl
    except Exception:
        pass
    return None


def main() -> None:
    bp = unreal.load_asset(CR_PATH)
    if not bp:
        print("load fail")
        return
    ctrl = get_controller(bp)
    if not ctrl:
        print("no ctrl")
        return

    section("1) dir(controller) — non-dunder")
    for n in sorted(dir(ctrl)):
        if not n.startswith("_"):
            print("  " + n)

    section("2) controller.get_graph() result")
    try:
        g = ctrl.get_graph()
        print("graph:", g)
        print("class:", g.get_class().get_name())
        print("\ndir(graph) — link/node/pin 포함:")
        for n in sorted(dir(g)):
            if n.startswith("_"):
                continue
            low = n.lower()
            if any(k in low for k in
                   ("link", "node", "pin", "connect", "child")):
                print("  " + n)
    except Exception as e:
        print("graph err:", e)
        return

    section("3) various node/link getters")
    for meth in [
        "get_nodes", "get_links",
        "get_node_names", "get_all_nodes",
        "get_local_variables",
    ]:
        try:
            fn = getattr(g, meth, None)
            if not callable(fn):
                print(f"  {meth}: not found")
                continue
            val = fn()
            n = len(val) if hasattr(val, "__len__") else "(?)"
            print(f"  {meth} -> {n} items   type={type(val).__name__}")
            if val and hasattr(val, "__iter__"):
                first = list(val)[0]
                print(f"    first: {first}  (class={type(first).__name__})")
        except Exception as e:
            print(f"  {meth} err: {type(e).__name__}: {str(e)[:80]}")

    section("4) get_nodes -> per-node pin/link")
    try:
        nodes = list(g.get_nodes())
        print(f"nodes count = {len(nodes)}")
        clamp = None
        for n in nodes:
            try:
                nn = n.get_node_title() if hasattr(n, "get_node_title") else ""
                name = n.get_name() if hasattr(n, "get_name") else ""
                if "Clamp" in str(nn) or "Clamp" in name:
                    clamp = n
                    break
            except Exception:
                continue
        if not clamp and nodes:
            clamp = nodes[0]
        print(f"inspect node: {clamp}")
        print("dir(node) — pin/link/connect:")
        for nm in sorted(dir(clamp)):
            if nm.startswith("_"):
                continue
            low = nm.lower()
            if any(k in low for k in
                   ("pin", "link", "connect", "node_name",
                    "node_title", "node_path")):
                print("  " + nm)

        # try get_pins
        for meth in ("get_pins", "get_all_pins"):
            try:
                fn = getattr(clamp, meth, None)
                if not callable(fn):
                    continue
                pins = list(fn())
                print(f"\n{meth} -> {len(pins)} pins")
                if pins:
                    p = pins[0]
                    print(f"first pin: {p}")
                    print("dir(pin) — link/connect/source/target:")
                    for pn in sorted(dir(p)):
                        if pn.startswith("_"):
                            continue
                        low = pn.lower()
                        if any(k in low for k in
                               ("link", "connect", "source", "target",
                                "pin_path", "name", "direction")):
                            print("  " + pn)
                    break
            except Exception as e:
                print(f"{meth} err: {e}")
    except Exception as e:
        print("nodes err:", e)


main()
