"""ID hardcoding 제거 — 이름·기능 기반 노드 lookup.

기존 패턴:
    connect("K2Node_VariableGet_72", "Velocity", ...)   # 백업 ID hardcoded

개선:
    vg_id = find_var_get(graph_data, "Velocity")
    connect(vg_id, "Velocity", ...)

ABP 재컴파일·복원 시 ID가 바뀌어도 깨지지 않음.
"""
from __future__ import annotations

from typing import Any

from .monolith_client import call_blueprint


def get_graph_data(asset_path: str, graph_name: str) -> dict | None:
    """Dump full graph data dict (nodes[], etc)."""
    r = call_blueprint("get_graph_data", {
        "asset_path": asset_path, "graph_name": graph_name,
    })
    if not r or (isinstance(r, dict) and "_error" in r):
        return None
    return r if isinstance(r, dict) else None


def find_node_by_variable(graph_data: dict, var_name: str, kind: str = "any") -> str | None:
    """Find first K2Node_VariableGet/Set whose title contains var_name.

    kind: "get" / "set" / "any"
    """
    prefix_map = {"get": "Get ", "set": "Set "}
    target_prefix = prefix_map.get(kind)
    target_classes = {
        "get": "K2Node_VariableGet",
        "set": "K2Node_VariableSet",
    }
    for n in graph_data.get("nodes", []):
        cls = n.get("class", "")
        title = n.get("title", "")
        if kind != "any" and cls != target_classes.get(kind):
            continue
        if target_prefix and not title.startswith(target_prefix):
            continue
        # title format: "Get Velocity" or "Set Speed2D"
        if title.endswith(var_name) or var_name in title:
            return n.get("id")
    return None


def find_var_get(graph_data: dict, var_name: str) -> str | None:
    return find_node_by_variable(graph_data, var_name, kind="get")


def find_var_set(graph_data: dict, var_name: str) -> str | None:
    return find_node_by_variable(graph_data, var_name, kind="set")


def find_node_by_function(
    graph_data: dict,
    fn_name: str,
    fn_class: str | None = None,
) -> str | None:
    """Find first CallFunction-like node by function name (and optional class)."""
    func_classes = {
        "K2Node_CallFunction",
        "K2Node_CallArrayFunction",
        "K2Node_CommutativeAssociativeBinaryOperator",
        "K2Node_PromotableOperator",
    }
    for n in graph_data.get("nodes", []):
        if n.get("class") not in func_classes:
            continue
        if n.get("function") != fn_name:
            continue
        if fn_class and n.get("function_class") != fn_class:
            continue
        return n.get("id")
    return None


def find_all_var_gets(graph_data: dict, var_name: str) -> list[str]:
    """Return all K2Node_VariableGet IDs that match var_name (multiple instances)."""
    out = []
    for n in graph_data.get("nodes", []):
        if n.get("class") != "K2Node_VariableGet":
            continue
        title = n.get("title", "")
        if title.endswith(var_name) or var_name in title:
            out.append(n.get("id"))
    return out


def find_node_by_class(graph_data: dict, cls: str) -> list[str]:
    """All nodes of a given class (Comment, Knot, IfThenElse, etc)."""
    return [n.get("id") for n in graph_data.get("nodes", []) if n.get("class") == cls]


def get_pin(node_dict: dict, pin_name: str, direction: str | None = None) -> dict | None:
    """Find a specific pin on a node."""
    for p in node_dict.get("pins", []):
        if p.get("name") != pin_name:
            continue
        if direction and p.get("direction") != direction:
            continue
        return p
    return None
