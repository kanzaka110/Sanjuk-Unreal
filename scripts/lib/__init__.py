"""scripts/lib — MCP-First Workflow Architecture, Layer ② Abstraction.

Re-exports the most commonly used helpers so individual scripts can
do `from lib import rpc, find_node_by_variable, bulk_connect`.
"""
from .monolith_client import rpc, call_blueprint, call_animation, call_chooser
from .node_lookup import (
    find_node_by_variable,
    find_node_by_function,
    find_var_get,
    find_var_set,
    get_graph_data,
)
from .bulk_ops import (
    bulk_connect,
    bulk_disconnect,
    bulk_set_pin_default,
    bulk_remove_nodes,
    build_format_text,
)
from .workflow_decorators import backup_apply_verify, with_dry_run, with_retry

__all__ = [
    "rpc", "call_blueprint", "call_animation", "call_chooser",
    "find_node_by_variable", "find_node_by_function",
    "find_var_get", "find_var_set", "get_graph_data",
    "bulk_connect", "bulk_disconnect", "bulk_set_pin_default",
    "bulk_remove_nodes", "build_format_text",
    "backup_apply_verify", "with_dry_run", "with_retry",
]
