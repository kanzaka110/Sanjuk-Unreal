"""Workflow decorators — backup-apply-verify, dry-run, retry.

사용 예:

    @backup_apply_verify(asset='/Game/.../PC_01_ABP', graph='UpdateVariables', tag='sprint_start')
    def add_sprint_start_chain():
        # 실제 작업 - rpc 호출 등
        ...

    add_sprint_start_chain()
    # → 자동: pre dump → 작업 → compile → save → post dump → diff JSON
"""
from __future__ import annotations

import functools
import json
import os
import time
from datetime import datetime
from typing import Callable

from .monolith_client import call_blueprint, compile_and_save
from .node_lookup import get_graph_data


SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKUP_DIR = os.path.join(SCRIPT_DIR, "backup")


def backup_apply_verify(
    asset: str,
    graph: str,
    tag: str = "",
    skip_compile: bool = False,
):
    """Decorator: dump pre → run fn → compile/save → dump post → diff.

    Saves backups to scripts/backup/<graph>_pre_<tag>_<date>.json etc.
    Returns dict {success, diff, ...} appended to the wrapped fn's return.
    """
    def deco(fn: Callable):
        @functools.wraps(fn)
        def wrapped(*args, **kwargs):
            os.makedirs(BACKUP_DIR, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            tag_part = f"_{tag}" if tag else ""

            # Pre dump
            pre = get_graph_data(asset, graph)
            pre_path = os.path.join(BACKUP_DIR, f"{graph}_pre{tag_part}_{stamp}.json")
            if pre:
                with open(pre_path, "w", encoding="utf-8") as f:
                    json.dump(pre, f, indent=2, ensure_ascii=False)
                print(f"[backup] pre dump → {pre_path}")
            else:
                print(f"[backup] WARNING: pre dump failed for {graph}")

            # Run user function
            t0 = time.time()
            user_result = fn(*args, **kwargs)
            elapsed = time.time() - t0

            # Compile + save
            compile_info = None
            if not skip_compile:
                ok, compile_info = compile_and_save(asset)
                if not ok:
                    print(f"[backup] WARNING: compile/save failed: {compile_info}")
                    return {
                        "user_result": user_result,
                        "elapsed_s": elapsed,
                        "compile_info": compile_info,
                        "success": False,
                    }

            # Post dump
            post = get_graph_data(asset, graph)
            post_path = os.path.join(BACKUP_DIR, f"{graph}_post{tag_part}_{stamp}.json")
            if post:
                with open(post_path, "w", encoding="utf-8") as f:
                    json.dump(post, f, indent=2, ensure_ascii=False)
                print(f"[backup] post dump → {post_path}")

            # Simple diff (node count delta)
            diff = None
            if pre and post:
                diff = {
                    "pre_nodes": len(pre.get("nodes", [])),
                    "post_nodes": len(post.get("nodes", [])),
                    "delta": len(post.get("nodes", [])) - len(pre.get("nodes", [])),
                }
                print(f"[backup] node delta: {diff['pre_nodes']} → {diff['post_nodes']} ({diff['delta']:+d})")

            return {
                "user_result": user_result,
                "elapsed_s": elapsed,
                "compile_info": compile_info,
                "diff": diff,
                "success": True,
            }
        return wrapped
    return deco


def with_dry_run(fn: Callable):
    """Decorator: if env DRY_RUN=1, just print intent and skip real call."""
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        if os.environ.get("DRY_RUN") == "1":
            print(f"[DRY] would call {fn.__name__}({args}, {kwargs})")
            return None
        return fn(*args, **kwargs)
    return wrapped


def with_retry(retries: int = 3, delay: float = 0.5):
    """Decorator: retry on exception."""
    def deco(fn: Callable):
        @functools.wraps(fn)
        def wrapped(*args, **kwargs):
            last = None
            for attempt in range(retries):
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:
                    last = exc
                    if attempt < retries - 1:
                        time.sleep(delay * (attempt + 1))
            raise last
        return wrapped
    return deco
