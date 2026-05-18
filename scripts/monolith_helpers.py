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

    # ── 백업 / 롤백 ─────────────────────────────────────────────────────
    @staticmethod
    def _asset_slug(asset: str) -> str:
        return asset.rsplit("/", 1)[-1].split(".")[0]

    def _backup_root(self) -> str:
        import os

        here = os.path.dirname(os.path.abspath(__file__))
        repo = os.path.dirname(here)
        return os.path.join(repo, ".claude", "state", "backups", self._asset_slug(self.asset))

    def backup(self, label: str = "") -> dict:
        """현재 ABP 상태 5종 dump 묶음 저장. timestamp + label 디렉토리.

        구성: abp_info / state_machines / transitions / variables / graphs(목록만)
        용도: Tuner 변경 적용 직전 자동 호출. 변경 후 rollback 가능.
        """
        import json
        import os
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = timestamp + (f"_{label}" if label else "")
        out_dir = os.path.join(self._backup_root(), slug)
        os.makedirs(out_dir, exist_ok=True)

        snapshot: dict[str, Any] = {
            "_meta": {
                "asset": self.asset,
                "timestamp": timestamp,
                "label": label,
                "created_at": datetime.now().isoformat(),
            },
            "abp_info": self.get_abp_info(),
            "state_machines": self.get_state_machines(),
            "transitions": self.get_transitions(),
            "variables": self.get_variables(),
        }
        for key, data in snapshot.items():
            if key == "_meta":
                continue
            with open(os.path.join(out_dir, f"{key}.json"), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        with open(os.path.join(out_dir, "_meta.json"), "w", encoding="utf-8") as f:
            json.dump(snapshot["_meta"], f, indent=2, ensure_ascii=False)

        return {
            "path": out_dir,
            "timestamp": timestamp,
            "label": label,
            "asset": self.asset,
            "files": 5,
        }

    def list_backups(self) -> list[dict]:
        """이 asset 에 대한 백업 목록 (timestamp 역순)."""
        import json
        import os

        root = self._backup_root()
        if not os.path.isdir(root):
            return []
        out = []
        for name in sorted(os.listdir(root), reverse=True):
            meta_path = os.path.join(root, name, "_meta.json")
            if not os.path.isfile(meta_path):
                continue
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            meta["dir"] = os.path.join(root, name)
            out.append(meta)
        return out

    def diff_against_backup(self, timestamp_or_label: str) -> dict:
        """현재 dump vs 백업 비교. 변수 default / SM transition count / graph 노드 수 차이 요약."""
        import json
        import os

        target_dir = None
        for entry in self.list_backups():
            name = os.path.basename(entry["dir"])
            if timestamp_or_label in name:
                target_dir = entry["dir"]
                break
        if not target_dir:
            raise MonolithError(f"백업 {timestamp_or_label!r} 못 찾음")

        with open(os.path.join(target_dir, "abp_info.json"), "r", encoding="utf-8") as f:
            old_info = json.load(f)
        with open(os.path.join(target_dir, "variables.json"), "r", encoding="utf-8") as f:
            old_vars = json.load(f)
        with open(os.path.join(target_dir, "state_machines.json"), "r", encoding="utf-8") as f:
            old_sms = json.load(f)

        new_info = self.get_abp_info()
        new_vars = self.get_variables()
        new_sms = self.get_state_machines()

        def var_default_map(payload: dict) -> dict[str, Any]:
            out: dict[str, Any] = {}
            for v in payload.get("variables", []) if isinstance(payload, dict) else []:
                if isinstance(v, dict):
                    out[v.get("name", "?")] = v.get("default")
            return out

        old_defaults = var_default_map(old_vars)
        new_defaults = var_default_map(new_vars)

        added_vars = sorted(set(new_defaults) - set(old_defaults))
        removed_vars = sorted(set(old_defaults) - set(new_defaults))
        changed_vars = sorted(
            n for n in (set(old_defaults) & set(new_defaults))
            if old_defaults[n] != new_defaults[n]
        )

        return {
            "backup_dir": target_dir,
            "abp_meta_changed": {
                "variable_count": [old_info.get("variable_count"), new_info.get("variable_count")],
                "graph_count":    [old_info.get("graph_count"),    new_info.get("graph_count")],
                "sm_count":       [old_info.get("state_machine_count"), new_info.get("state_machine_count")],
            },
            "variables_added": added_vars,
            "variables_removed": removed_vars,
            "variables_changed_default": changed_vars,
            "sm_transition_count_old": sum(
                sm.get("transition_count", 0)
                for sm in old_sms.get("state_machines", [])
            ),
            "sm_transition_count_new": sum(
                sm.get("transition_count", 0)
                for sm in new_sms.get("state_machines", [])
            ),
        }

    # ── 시각 검증 / 스크린샷 ──────────────────────────────────────────────
    def screenshot(
        self,
        resolution: tuple[int, int] = (1920, 1080),
        label: str = "",
        sb2_project_root: str = r"E:\Perforce\SB2\Workspace\Internal\SB2",
        copy_to: str | None = None,
    ) -> dict:
        """현재 viewport (또는 PIE) HighResShot 캡처.

        흐름:
          1. editor.run_console_command("HighResShot WxH") 호출
          2. <project>/Saved/Screenshots/WindowsEditor/HighresScreenshot*.png 폴링
          3. 최근 파일 path 반환 (copy_to 지정 시 그쪽으로 복사 + rename)

        AI 가 결과 path 를 `Read` 로 multimodal 분석 가능. [[feedback-visual-mesh-over-anim-rec]]
        의 "시각이 진짜 기준" 원칙 자동화.

        한계:
          - PIE 가 안 돌면 에디터 viewport (보통 빈 레벨) 만 캡처
          - PC_01 캐릭터 시각 검증은 PIE 시작 후 호출 필수
          - SB2 P4 워크스페이스 외 경로면 sb2_project_root 인자로 override
        """
        import os
        import shutil
        import time
        from datetime import datetime

        screenshots_dir = os.path.join(
            sb2_project_root, "Saved", "Screenshots", "WindowsEditor"
        )
        before = {
            f: os.path.getmtime(os.path.join(screenshots_dir, f))
            for f in (os.listdir(screenshots_dir) if os.path.isdir(screenshots_dir) else [])
            if f.lower().endswith(".png")
        }
        t_start = time.time()
        cmd_result = self.editor(
            "run_console_command", command=f"HighResShot {resolution[0]}x{resolution[1]}"
        )
        # 새 파일 폴링 (최대 5초)
        new_path = None
        for _ in range(50):
            time.sleep(0.1)
            if not os.path.isdir(screenshots_dir):
                continue
            for f in os.listdir(screenshots_dir):
                if not f.lower().endswith(".png"):
                    continue
                p = os.path.join(screenshots_dir, f)
                mt = os.path.getmtime(p)
                if mt > t_start - 1 and (f not in before or mt > before[f] + 0.1):
                    new_path = p
                    break
            if new_path:
                break

        result = {
            "command_result": cmd_result,
            "resolution": list(resolution),
            "label": label,
            "captured_path": new_path,
            "elapsed_seconds": round(time.time() - t_start, 2),
        }
        if new_path and copy_to:
            os.makedirs(copy_to, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            slug = f"{timestamp}{'_' + label if label else ''}.png"
            dest = os.path.join(copy_to, slug)
            shutil.copy2(new_path, dest)
            result["copied_to"] = dest
        return result

    def rollback(self, timestamp_or_label: str, dry_run: bool = True) -> dict:
        """백업의 변수 default 값으로 복원. dry_run=True 면 적용 계획만 출력.

        주의: 변수 default 복원만 안전. 노드/그래프 구조 복원은 사용자가 에디터에서 수동.
        그래프 토폴로지 변경 (노드 add/remove) 은 본 메서드 범위 외.
        """
        diff = self.diff_against_backup(timestamp_or_label)
        plan = {
            "asset": self.asset,
            "backup_dir": diff["backup_dir"],
            "dry_run": dry_run,
            "operations": [],
            "unsupported": [],
        }
        # 변수 default 복원
        import json
        import os

        with open(os.path.join(diff["backup_dir"], "variables.json"), "r", encoding="utf-8") as f:
            old_vars = json.load(f)
        old_defaults: dict[str, Any] = {}
        for v in old_vars.get("variables", []) if isinstance(old_vars, dict) else []:
            if isinstance(v, dict):
                old_defaults[v.get("name", "?")] = v.get("default")

        for vname in diff["variables_changed_default"]:
            old_val = old_defaults.get(vname)
            plan["operations"].append({
                "type": "set_variable_default",
                "variable": vname,
                "to": old_val,
            })

        if diff["variables_added"]:
            plan["unsupported"].append({
                "type": "remove_variable_to_match_backup",
                "variables": diff["variables_added"],
                "reason": "신규 변수 자동 제거는 위험 — 사용자가 수동 결정",
            })
        if diff["variables_removed"]:
            plan["unsupported"].append({
                "type": "re_add_variable_with_default",
                "variables": diff["variables_removed"],
                "reason": "변수 type 정보 손실 가능 — 사용자가 수동 결정",
            })
        if diff["sm_transition_count_old"] != diff["sm_transition_count_new"]:
            plan["unsupported"].append({
                "type": "state_machine_transition_topology",
                "delta": diff["sm_transition_count_new"] - diff["sm_transition_count_old"],
                "reason": "SM transition 구조 복원은 Monolith 한계 — 사용자가 에디터 수동",
            })

        if not dry_run:
            applied = []
            for op in plan["operations"]:
                if op["type"] == "set_variable_default":
                    try:
                        result = self.bp(
                            "set_variable_defaults",
                            variable_name=op["variable"],
                            default_value=op["to"],
                        )
                        applied.append({"op": op, "result": result})
                    except MonolithError as exc:
                        applied.append({"op": op, "error": str(exc)})
            plan["applied"] = applied
            plan["commit"] = self.commit()

        return plan


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
