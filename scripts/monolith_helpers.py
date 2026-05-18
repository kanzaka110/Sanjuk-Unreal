"""Monolith HTTP RPC 공통 헬퍼.

scripts/ 137 파일 중 절대 다수가 같은 boilerplate (rpc 함수 / add_node / connect_pins /
compile_blueprint / save_asset) 를 복붙해 쓰고 있다. 이 모듈로 신규 스크립트의 헤더가
3 import + 1 ASSET 상수로 줄어든다.

기존 137 스크립트는 손대지 않는다 (P4/메모리 상태 기준선이라 동결).
새 작업부터 다음처럼 사용:

    from monolith_helpers import MonolithClient

    cli = MonolithClient(asset="/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP")
    cli.add_node("AnimGraph", "VariableGet", [0, 0], variable_name="IsTransition")
    cli.connect_pins("AnimGraph", src_node, "Pose", tgt_node, "Result")
    cli.compile()
    cli.save()

API는 blueprint_query / animation_query 두 도메인을 다 wrap.
"""
from __future__ import annotations

import json
import urllib.request
from typing import Any

ENDPOINT_DEFAULT = "http://localhost:9316/mcp"


class MonolithError(RuntimeError):
    """RPC error / isError true / dict 'error' 키 응답."""


class MonolithClient:
    """단일 ABP/BP 에셋을 대상으로 하는 thin RPC wrapper.

    asset 을 지정하면 모든 호출에 asset_path 인자가 자동 주입된다. 다른 asset
    에 일회성 호출이 필요하면 키워드로 asset_path 를 직접 넘기면 override.
    """

    def __init__(
        self,
        asset: str,
        endpoint: str = ENDPOINT_DEFAULT,
        timeout: float = 30.0,
    ) -> None:
        self.asset = asset
        self.endpoint = endpoint
        self.timeout = timeout
        self._id = 0

    # ── 기본 RPC ────────────────────────────────────────────────────────
    def rpc(
        self,
        tool: str,
        action: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """원시 RPC. 응답 content[0].text 가 JSON 이면 parse, 아니면 raw."""
        self._id += 1
        p = dict(params or {})
        p.setdefault("asset_path", self.asset)
        body = {
            "jsonrpc": "2.0",
            "id": self._id,
            "method": "tools/call",
            "params": {
                "name": tool,
                "arguments": {"action": action, "params": p},
            },
        }
        req = urllib.request.Request(
            self.endpoint,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("error"):
            raise MonolithError(f"{tool}.{action}: {data['error']}")
        result = data.get("result", {})
        if result.get("isError"):
            txt = result["content"][0]["text"][:400] if result.get("content") else "(empty)"
            raise MonolithError(f"{tool}.{action} isError: {txt}")
        content = result.get("content") or []
        if not content:
            return None
        text = content[0].get("text", "")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text

    # 자주 쓰는 도메인 short-form
    def bp(self, action: str, **params: Any) -> Any:
        return self.rpc("blueprint_query", action, params)

    def anim(self, action: str, **params: Any) -> Any:
        return self.rpc("animation_query", action, params)

    def editor(self, action: str, **params: Any) -> Any:
        return self.rpc("editor_query", action, params)

    # ── ABP / BP 편집 (top-5 사용 액션 wrap) ─────────────────────────────
    def add_node(
        self,
        graph_name: str,
        node_type: str,
        position: tuple[float, float] | list[float],
        **extra: Any,
    ) -> dict:
        return self.bp(
            "add_node",
            graph_name=graph_name,
            node_type=node_type,
            position=list(position),
            **extra,
        )

    def remove_node(self, graph_name: str, node_id: str) -> dict:
        return self.bp("remove_node", graph_name=graph_name, node_id=node_id)

    def connect_pins(
        self,
        graph_name: str,
        source_node: str,
        source_pin: str,
        target_node: str,
        target_pin: str,
    ) -> dict:
        return self.bp(
            "connect_pins",
            graph_name=graph_name,
            source_node=source_node,
            source_pin=source_pin,
            target_node=target_node,
            target_pin=target_pin,
        )

    def disconnect_pins(
        self,
        graph_name: str,
        source_node: str,
        source_pin: str,
        target_node: str,
        target_pin: str,
    ) -> dict:
        return self.bp(
            "disconnect_pins",
            graph_name=graph_name,
            source_node=source_node,
            source_pin=source_pin,
            target_node=target_node,
            target_pin=target_pin,
        )

    def set_pin_default(
        self,
        graph_name: str,
        node_id: str,
        pin_name: str,
        value: Any,
    ) -> dict:
        return self.bp(
            "set_pin_default",
            graph_name=graph_name,
            node_id=node_id,
            pin_name=pin_name,
            default_value=value,
        )

    def compile(self) -> dict:
        return self.bp("compile_blueprint")

    def validate(self) -> dict:
        return self.bp("validate_blueprint")

    def save(self) -> dict:
        """save_asset. P4 잠금 시 'Failed' 응답 + 에디터 Ctrl+S 가능."""
        return self.bp("save_asset")

    # ── 조회 ───────────────────────────────────────────────────────────
    def get_graph_data(self, graph_name: str) -> dict:
        return self.bp("get_graph_data", graph_name=graph_name)

    def get_node_details(self, graph_name: str, node_id: str) -> dict:
        return self.bp(
            "get_node_details", graph_name=graph_name, node_id=node_id
        )

    def get_variables(self) -> dict:
        return self.bp("get_variables")

    def get_abp_info(self) -> dict:
        return self.anim("get_abp_info")

    def get_state_machines(self) -> dict:
        return self.anim("get_state_machines")

    def get_transitions(self, machine_name: str | None = None) -> dict:
        params: dict[str, Any] = {}
        if machine_name:
            params["machine_name"] = machine_name
        return self.anim("get_transitions", **params)

    # ── AnimGraph 노드 ─────────────────────────────────────────────────
    def add_anim_graph_node(
        self,
        node_type: str,
        graph_name: str = "AnimGraph",
        position: tuple[float, float] | list[float] = (0, 0),
        **extra: Any,
    ) -> dict:
        return self.anim(
            "add_anim_graph_node",
            node_type=node_type,
            graph_name=graph_name,
            position_x=position[0],
            position_y=position[1],
            **extra,
        )

    def connect_anim_graph_pins(
        self,
        source_node: str,
        source_pin: str,
        target_node: str,
        target_pin: str,
        graph_name: str = "AnimGraph",
        compile: bool = True,
    ) -> dict:
        return self.anim(
            "connect_anim_graph_pins",
            source_node=source_node,
            source_pin=source_pin,
            target_node=target_node,
            target_pin=target_pin,
            graph_name=graph_name,
            compile=compile,
        )

    # ── 변수 ───────────────────────────────────────────────────────────
    def add_variable(self, name: str, var_type: str, default: Any = None) -> dict:
        params: dict[str, Any] = {"variable_name": name, "variable_type": var_type}
        if default is not None:
            params["default_value"] = default
        return self.bp("add_variable", **params)

    def remove_variable(self, name: str) -> dict:
        return self.bp("remove_variable", variable_name=name)

    # ── 헬퍼: compile + save 한 번에 ────────────────────────────────────
    def commit(self, do_validate: bool = True) -> dict:
        """compile → validate (옵션) → save 순차. save 실패해도 결과 반환."""
        out = {"compile": self.compile()}
        if do_validate:
            out["validate"] = self.validate()
        try:
            out["save"] = self.save()
        except MonolithError as exc:
            out["save"] = {"error": str(exc), "hint": "P4 잠금 가능 — 에디터 Ctrl+S"}
        return out


# ── 모듈 단독 실행: 헬퍼 동작 smoke test ────────────────────────────────
if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="MonolithClient smoke test")
    ap.add_argument(
        "--asset",
        default="/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP",
        help="대상 ABP 경로",
    )
    args = ap.parse_args()

    cli = MonolithClient(args.asset)
    info = cli.get_abp_info()
    print(f"asset    : {args.asset}")
    print(f"skeleton : {info.get('skeleton')}")
    print(f"SM       : {info.get('state_machine_count')}")
    print(f"graphs   : {info.get('graph_count')}")
    print(f"vars     : {info.get('variable_count')}")
    print("smoke OK")
