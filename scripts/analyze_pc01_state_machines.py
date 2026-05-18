#!/usr/bin/env python3
"""PC_01_ABP State Machine 종합 dump (Monolith animation_query 백엔드).

기존 dump_animgraph_nodes.py / parse_animgraph_t3d.py 는 T3D 텍스트를 paste 받아
정규식으로 파싱한다. 이 스크립트는 Monolith 의 animation_query API 를 직접 호출해
SM 구조와 transition rule 노드 chain 까지 한 번에 받는다.

장점:
  - T3D copy-paste 불필요 (자산 path 만 있으면 됨)
  - 한글 코멘트 / rule_nodes / state_count / cross_fade_duration 모두 구조화
  - rule_nodes 가 K2Node class + title 까지 들어옴 → 조건 의도 가독성

출력:
  dumps/sm/<ASSET_NAME>_abp_info.json
  dumps/sm/<ASSET_NAME>_state_machines.json
  dumps/sm/<ASSET_NAME>_transitions.json
  dumps/sm/<ASSET_NAME>_linked_assets.json
  dumps/sm/<ASSET_NAME>_summary.md  (사람이 읽는 요약)

사용:
  py scripts/analyze_pc01_state_machines.py
  py scripts/analyze_pc01_state_machines.py --asset /Game/Art/Character/.../OtherABP
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime

DEFAULT_ASSET = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
ENDPOINT = "http://localhost:9316/mcp"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)


class MonolithError(RuntimeError):
    pass


def rpc(action: str, params: dict) -> dict:
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "animation_query",
            "arguments": {"action": action, "params": params},
        },
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if data.get("error"):
        raise MonolithError(str(data["error"]))
    result = data.get("result", {})
    if result.get("isError"):
        raise MonolithError(result["content"][0]["text"][:400])
    return json.loads(result["content"][0]["text"])


def asset_name(asset_path: str) -> str:
    return asset_path.rsplit("/", 1)[-1].split(".")[0]


def dump_all(asset_path: str, out_dir: str) -> dict:
    """4개 액션을 호출해서 JSON 4개 + 요약 .md 저장. 통계 dict 반환."""
    os.makedirs(out_dir, exist_ok=True)
    name = asset_name(asset_path)

    print(f"asset : {asset_path}")
    print(f"out   : {out_dir}")
    print()

    payloads = {
        "abp_info":       rpc("get_abp_info",         {"asset_path": asset_path}),
        "state_machines": rpc("get_state_machines",   {"asset_path": asset_path}),
        "transitions":    rpc("get_transitions",      {"asset_path": asset_path}),
        "linked_assets":  rpc("get_abp_linked_assets",{"asset_path": asset_path}),
    }

    for key, data in payloads.items():
        path = os.path.join(out_dir, f"{name}_{key}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  ✓ {key:14s} → {path}")

    summary_path = os.path.join(out_dir, f"{name}_summary.md")
    write_summary(summary_path, asset_path, payloads)
    print(f"  ✓ summary        → {summary_path}")

    return {
        "asset_path": asset_path,
        "state_machine_count": payloads["abp_info"].get("state_machine_count", 0),
        "graph_count":         payloads["abp_info"].get("graph_count", 0),
        "variable_count":      payloads["abp_info"].get("variable_count", 0),
        "transition_count":    sum(
            sm.get("transition_count", 0)
            for sm in payloads["state_machines"].get("state_machines", [])
        ),
        "linked_assets_total": payloads["linked_assets"].get("total_dependencies", 0),
    }


def write_summary(path: str, asset_path: str, payloads: dict) -> None:
    info = payloads["abp_info"]
    sms = payloads["state_machines"].get("state_machines", [])
    trans = payloads["transitions"].get("transitions", [])
    linked = payloads["linked_assets"]

    lines: list[str] = []
    lines.append(f"# {asset_name(asset_path)} — Animation Blueprint 요약")
    lines.append("")
    lines.append(f"- asset_path: `{asset_path}`")
    lines.append(f"- generated:  {datetime.now().isoformat()}")
    lines.append(f"- skeleton:   `{info.get('skeleton')}`")
    lines.append(f"- parent:     `{info.get('parent_class')}`")
    lines.append(
        f"- 카운트:     SM {info.get('state_machine_count')} / "
        f"graphs {info.get('graph_count')} / "
        f"variables {info.get('variable_count')}"
    )
    lines.append(f"- interfaces: {', '.join(info.get('interfaces', [])) or '(none)'}")
    lines.append("")

    # 그래프 목록
    lines.append("## 그래프 목록")
    lines.append("")
    for g in info.get("graphs", []):
        lines.append(f"- `{g}`")
    lines.append("")

    # State Machines
    lines.append("## State Machines")
    lines.append("")
    for sm in sms:
        lines.append(f"### `{sm['name']}` (그래프: `{sm.get('graph')}`)")
        lines.append("")
        lines.append(f"- entry_state: **{sm.get('entry_state')}**")
        lines.append(f"- state_count: {sm.get('state_count')}")
        lines.append(f"- transition_count: {sm.get('transition_count')}")
        lines.append("")
        lines.append("**States:**")
        for s in sm.get("states", []):
            pos = s.get("position", [0, 0])
            lines.append(f"- `{s['name']}` @ ({pos[0]}, {pos[1]})")
        lines.append("")

    # Transitions (간단 요약 + rule 종합)
    lines.append("## Transitions 요약")
    lines.append("")
    lines.append(f"총 {len(trans)} 개. 각 transition 의 rule 노드 chain 은 _transitions.json 참조.")
    lines.append("")
    lines.append("| from | to | xfade(s) | rule node count |")
    lines.append("|---|---|---:|---:|")
    for t in trans:
        rn = len(t.get("rule_nodes", []))
        lines.append(
            f"| {t['from']} | {t['to']} | "
            f"{t.get('cross_fade_duration', 0):.3f} | {rn} |"
        )
    lines.append("")

    # Linked assets
    lines.append("## Linked Assets")
    lines.append("")
    lines.append(f"- total_dependencies: {linked.get('total_dependencies')}")
    for key in ("sequences", "montages", "blend_spaces", "composites", "linked_anim_blueprints"):
        items = linked.get(key, [])
        if not items:
            continue
        lines.append(f"\n**{key}** ({len(items)})")
        for it in items:
            lines.append(f"- `{it}`")
    lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--asset", default=DEFAULT_ASSET, help="ABP 자산 경로")
    ap.add_argument(
        "--out",
        default=os.path.join(REPO_ROOT, "dumps", "sm"),
        help="출력 디렉토리",
    )
    args = ap.parse_args()
    try:
        stats = dump_all(args.asset, args.out)
    except MonolithError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 2
    print()
    print("Stats:")
    for k, v in stats.items():
        print(f"  {k:22s} {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
