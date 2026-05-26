#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""5/22 transitions_v2 덤프 vs 현재 에디터 transition rule 정밀 비교 (롤백 영향 탐지).

- 현재값은 Monolith HTTP JSON-RPC (localhost:9316/mcp) get_transitions 로 실시간 취득.
- 5/22 기준: dumps/sm/PC_01_ABP_transitions_v2.json (19:02, 마지막 덤프).
- transition 순서가 두 덤프에서 동일(get_transitions 내부 순서)하므로 위치 정렬 비교.
- 각 rule 의 노드 title 시퀀스를 비교해 5/22 에만 있는 노드(=롤백으로 소실)를 출력.
"""
import json
import sys
import urllib.request

ASSET = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
MACHINE = "MoveStateMachine"
REF_PATH = r"C:/Dev/Sanjuk-Unreal/dumps/sm/PC_01_ABP_transitions_v2.json"
URL = "http://localhost:9316/mcp"


def call_monolith(action, params):
    payload = {
        "jsonrpc": "2.0", "method": "tools/call", "id": 1,
        "params": {"name": "animation_query",
                   "arguments": {"action": action, "params": params}},
    }
    req = urllib.request.Request(
        URL, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        resp = json.load(r)
    # MCP tools/call -> result.content[0].text (JSON 문자열)
    content = resp["result"]["content"][0]["text"]
    return json.loads(content)


def titles(rule_nodes):
    return [f"{n.get('class','?')}::{n.get('title','?')}" for n in rule_nodes]


def main():
    cur = call_monolith("get_transitions", {"asset_path": ASSET, "machine_name": MACHINE})
    with open(REF_PATH, encoding="utf-8") as f:
        ref = json.load(f)

    cur_t = cur["transitions"]
    ref_t = ref["transitions"]
    print(f"현재 transition 수: {len(cur_t)} / 5/22 덤프: {len(ref_t)}\n")

    if len(cur_t) != len(ref_t):
        print("⚠ transition 개수 불일치 — 위치 정렬 비교가 부정확할 수 있음\n")

    n = min(len(cur_t), len(ref_t))
    diff_count = 0
    for i in range(n):
        c, r = cur_t[i], ref_t[i]
        ct, rt = titles(c.get("rule_nodes", [])), titles(r.get("rule_nodes", []))
        label = f"#{i:02d} {r.get('from')} -> {r.get('to')}"
        if c.get("from") != r.get("from") or c.get("to") != r.get("to"):
            print(f"[순서불일치] {label}  (현재: {c.get('from')}->{c.get('to')})")
        if ct == rt:
            continue
        diff_count += 1
        # multiset 차이
        from collections import Counter
        cc, rc = Counter(ct), Counter(rt)
        lost = list((rc - cc).elements())     # 5/22 에 있었으나 현재 없음 = 롤백 소실
        added = list((cc - rc).elements())    # 현재 추가됨 (롤백 후 더 생긴 것)
        print(f"=== {label}  (5/22 {len(rt)}개 -> 현재 {len(ct)}개) ===")
        if lost:
            print(f"  ❌ 소실(5/22에 있던 노드, 복원 대상) [{len(lost)}]:")
            for x in lost:
                print(f"      - {x}")
        if added:
            print(f"  ＋ 현재에만 있음 [{len(added)}]:")
            for x in added:
                print(f"      + {x}")
        print()

    print(f"\n총 {diff_count}/{n} transition rule 이 5/22와 다름.")


if __name__ == "__main__":
    main()
