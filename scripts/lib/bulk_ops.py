"""Bulk wire / disconnect / set_default — 65개 wire를 한 번에.

기존 step2.py 가 65개 connect를 직접 순차 호출했지만,
여기서는 list[Wire] 받아서 한 함수로 처리 + 결과 집계.

Future: Monolith가 정말 build_*_from_spec API를 제공하면 그걸로 swap.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .monolith_client import call_blueprint


@dataclass(frozen=True)
class Wire:
    src_node: str
    src_pin: str
    dst_node: str
    dst_pin: str


def bulk_connect(
    asset_path: str,
    graph_name: str,
    wires: Iterable[Wire | tuple],
    *,
    silent: bool = False,
) -> dict:
    """Apply all wires. Returns {ok: int, fail: int, failures: [Wire, err]}."""
    ok = fail = 0
    failures: list[tuple[Wire, str]] = []
    for w in wires:
        if isinstance(w, tuple):
            w = Wire(*w)
        r = call_blueprint("connect_pins", {
            "asset_path": asset_path,
            "graph_name": graph_name,
            "source_node": w.src_node, "source_pin": w.src_pin,
            "target_node": w.dst_node, "target_pin": w.dst_pin,
        }, silent=silent)
        if r is None or (isinstance(r, dict) and "_error" in r):
            fail += 1
            err = r.get("_error", "(no resp)") if isinstance(r, dict) else "(no resp)"
            failures.append((w, err[:120]))
        else:
            ok += 1
    return {"ok": ok, "fail": fail, "failures": failures}


def bulk_disconnect(
    asset_path: str,
    graph_name: str,
    wires: Iterable[Wire | tuple],
    *,
    silent: bool = False,
) -> dict:
    ok = fail = 0
    failures: list[tuple[Wire, str]] = []
    for w in wires:
        if isinstance(w, tuple):
            w = Wire(*w)
        r = call_blueprint("disconnect_pins", {
            "asset_path": asset_path,
            "graph_name": graph_name,
            "source_node": w.src_node, "source_pin": w.src_pin,
            "target_node": w.dst_node, "target_pin": w.dst_pin,
        }, silent=silent)
        if r is None or (isinstance(r, dict) and "_error" in r):
            fail += 1
            err = r.get("_error", "(no resp)") if isinstance(r, dict) else "(no resp)"
            failures.append((w, err[:120]))
        else:
            ok += 1
    return {"ok": ok, "fail": fail, "failures": failures}


def bulk_set_pin_default(
    asset_path: str,
    graph_name: str,
    pin_defaults: dict[tuple[str, str], str],
    *,
    silent: bool = False,
) -> dict:
    """pin_defaults: {(node_id, pin_name): value}."""
    ok = fail = 0
    failures: list[tuple[str, str, str]] = []
    for (nid, pname), val in pin_defaults.items():
        r = call_blueprint("set_pin_default", {
            "asset_path": asset_path,
            "graph_name": graph_name,
            "node_id": nid, "pin_name": pname, "value": str(val),
        }, silent=silent)
        if r is None or (isinstance(r, dict) and "_error" in r):
            fail += 1
            err = r.get("_error", "(no resp)") if isinstance(r, dict) else "(no resp)"
            failures.append((nid, pname, err[:120]))
        else:
            ok += 1
    return {"ok": ok, "fail": fail, "failures": failures}


def bulk_remove_nodes(
    asset_path: str,
    graph_name: str,
    node_ids: Iterable[str],
    *,
    compile_between: bool = False,
    silent: bool = False,
) -> dict:
    """Remove nodes one by one (compile between if requested - safer for large bulk)."""
    ok = fail = 0
    failures: list[tuple[str, str]] = []
    for nid in node_ids:
        r = call_blueprint("remove_node", {
            "asset_path": asset_path, "graph_name": graph_name, "node_id": nid,
        }, silent=silent)
        if r is None or (isinstance(r, dict) and "_error" in r):
            fail += 1
            err = r.get("_error", "(no resp)") if isinstance(r, dict) else "(no resp)"
            failures.append((nid, err[:120]))
            continue
        ok += 1
        if compile_between:
            c = call_blueprint("compile_blueprint", {"asset_path": asset_path}, silent=True)
            if c and isinstance(c, dict) and c.get("error_count", 0) > 0:
                # rollback unlikely; just report
                failures.append((nid, f"compile errors after delete: {c.get('errors')}"))
    return {"ok": ok, "fail": fail, "failures": failures}


def build_format_text(
    asset_path: str,
    graph_name: str,
    format_str: str,
    position: list[int],
) -> str | None:
    """Add a K2Node_FormatText with Format string. Returns new node id."""
    r = call_blueprint("add_node", {
        "asset_path": asset_path, "graph_name": graph_name,
        "node_type": "format_text",
        "position": position,
        "format": format_str,
    })
    if not r or (isinstance(r, dict) and "_error" in r):
        return None
    return r.get("node_id") or r.get("id") if isinstance(r, dict) else None
