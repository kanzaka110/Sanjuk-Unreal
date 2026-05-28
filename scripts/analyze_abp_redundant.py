#!/usr/bin/env python3
"""PC_01_ABP "불필요한 노드" 확장 탐지 — orphan 너머 패턴.

dumps/deadcode/<graph>.json (analyze_abp_deadcode.py 가 저장) 을 재읽어 추가 패턴:

  1. computed_dropped — 비-pure 노드 (exec 핀 보유) 가 exec 흐름엔 들어가지만
     모든 데이터 출력 핀이 비연결. "실행은 되지만 결과가 버려짐". 부작용 호출
     (Set Timer 등) 일 수 있어 사용자 판정 필요.

  2. unused_purchase — pure 노드 (exec 핀 없음) 중 모든 출력이 비연결.
     이미 analyze_abp_deadcode.py orphan 으로 잡혔으므로 중복 표시 안 함.

  3. dangling_input — 비-pure 노드의 데이터 입력 핀이 비연결 (기본값 사용).
     Set 노드의 value 입력 등 — 기본값 의도일 수 있어 참조용으로만 카운트.

  4. knot_chain — Knot 3개 이상 직렬. 단순 reroute 누적, 정리 가치.

  5. orphan_island — 노드 그룹이 전체 exec 그래프에서 단절 (entry 도달 불가).
     단일 노드는 1번 orphan 으로 잡힘. 2개 이상 island 만.

디버그 그래프 (DrawDebug, AnimRewindRecorderEmit) 는 노이즈라 제외.
"""
from __future__ import annotations

import json
import os
from collections import defaultdict, deque

DUMP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dumps", "deadcode")
DEBUG_GRAPHS = {"DrawDebug", "AnimRewindRecorderEmit"}

# 부작용 호출이라 ReturnValue dropped 가 정상인 함수 패턴 (오탐 방지).
SIDE_EFFECT_FUNC_HINTS = (
    "Set", "Add", "Remove", "Clear", "Reset", "Print", "Log", "Spawn",
    "Destroy", "Play", "Stop", "Apply", "Update", "Send", "Trigger",
    "Reload", "Save", "Notify",
)


def has_exec(pins: list[dict]) -> bool:
    return any(p.get("type") == "exec" for p in pins)


def exec_input_connected(pins: list[dict]) -> bool:
    for p in pins:
        if p.get("type") == "exec" and p.get("direction") == "input":
            if p.get("connected_to"):
                return True
    return False


def data_outputs(pins: list[dict]) -> list[dict]:
    return [p for p in pins if p.get("direction") == "output" and p.get("type") != "exec"]


def data_inputs(pins: list[dict]) -> list[dict]:
    return [p for p in pins if p.get("direction") == "input" and p.get("type") != "exec"]


def func_looks_side_effect(name: str | None) -> bool:
    if not name:
        return False
    for hint in SIDE_EFFECT_FUNC_HINTS:
        if name.startswith(hint):
            return True
    return False


def main() -> int:
    results: dict[str, dict] = {}
    for fn in sorted(os.listdir(DUMP_DIR)):
        if not fn.endswith(".json"):
            continue
        gname = fn[:-5].replace("_", " ")
        # 디버그 그래프 스킵
        if gname.replace(" ", "") in {g.replace(" ", "") for g in DEBUG_GRAPHS} or gname in DEBUG_GRAPHS:
            continue
        try:
            data = json.load(open(os.path.join(DUMP_DIR, fn), encoding="utf-8"))
        except Exception:
            continue
        nodes = data.get("nodes", [])
        if not nodes:
            continue

        computed_dropped: list[dict] = []
        knot_runs: list[list[str]] = []
        islands: list[list[str]] = []

        # 1. computed_dropped
        for n in nodes:
            pins = n.get("pins") or []
            if not has_exec(pins):
                continue  # pure → 이미 orphan 분석 대상
            if not exec_input_connected(pins):
                continue  # exec in 안 들어옴 → 어차피 안 실행됨 (orphan/도달불가)
            douts = data_outputs(pins)
            if not douts:
                continue  # 데이터 출력 없는 순수 흐름 노드 (Branch 등)
            all_dangling = all(not p.get("connected_to") for p in douts)
            if not all_dangling:
                continue
            cls = str(n.get("class", ""))
            func = n.get("function")
            is_side_effect = False
            if cls == "K2Node_CallFunction" and func_looks_side_effect(func):
                is_side_effect = True
            # VariableSet 의 Output_Get 만 dropped 인 케이스 → 일반적 (default behavior)
            if cls == "K2Node_VariableSet" and {p["name"] for p in douts} <= {"Output_Get"}:
                continue
            computed_dropped.append({
                "id": n.get("id"),
                "class": cls,
                "title": n.get("title"),
                "func": func,
                "pos": n.get("pos"),
                "outputs_dropped": [p["name"] for p in douts],
                "side_effect_hint": is_side_effect,
            })

        # 2. knot chain 검출
        node_by_id = {n["id"]: n for n in nodes}
        for n in nodes:
            if n.get("class") != "K2Node_Knot":
                continue
            # 시작 knot 만 (이전이 knot 가 아닐 때) 체인 추적
            pins = n.get("pins") or []
            input_pin = next((p for p in pins if p["direction"] == "input"), None)
            if not input_pin:
                continue
            srcs = [s.split(".")[0] for s in (input_pin.get("connected_to") or [])]
            if any(node_by_id.get(s, {}).get("class") == "K2Node_Knot" for s in srcs):
                continue  # 체인 중간
            chain = [n["id"]]
            cur = n
            visited = {cur["id"]}
            while True:
                out_pin = next((p for p in cur.get("pins", []) if p["direction"] == "output"), None)
                if not out_pin:
                    break
                tgts = [t.split(".")[0] for t in (out_pin.get("connected_to") or [])]
                next_knots = [
                    node_by_id[t] for t in tgts
                    if node_by_id.get(t, {}).get("class") == "K2Node_Knot" and t not in visited
                ]
                if not next_knots:
                    break
                cur = next_knots[0]
                visited.add(cur["id"])
                chain.append(cur["id"])
            if len(chain) >= 3:
                knot_runs.append(chain)

        # 3. orphan island 검출: 모든 비연결 컴포넌트 중 entry 미포함 + 노드 ≥2
        # AnimGraph 는 패러다임 (Pose 핀 / Root sink) 이 달라 오탐 → 스킵.
        if gname == "AnimGraph":
            if computed_dropped or knot_runs:
                results[gname] = {"computed_dropped": computed_dropped, "knot_runs": knot_runs, "islands": []}
            continue
        # 인접: pins[*].connected_to 의 다른 노드.
        adj: dict[str, set[str]] = defaultdict(set)
        for n in nodes:
            nid = n.get("id")
            for p in n.get("pins") or []:
                for t in p.get("connected_to") or []:
                    tid = t.split(".")[0]
                    adj[nid].add(tid)
                    adj[tid].add(nid)
        entries = {n["id"] for n in nodes if n.get("class") in ("K2Node_FunctionEntry", "K2Node_Event", "K2Node_CustomEvent")}
        seen: set[str] = set()
        for n in nodes:
            nid = n.get("id")
            if nid in seen:
                continue
            queue: deque[str] = deque([nid])
            component: list[str] = []
            while queue:
                x = queue.popleft()
                if x in seen:
                    continue
                seen.add(x)
                component.append(x)
                for y in adj[x]:
                    if y not in seen:
                        queue.append(y)
            # entry 미포함이고 노드 ≥2 (단일 노드는 orphan 분석에 잡힘)
            if len(component) >= 2 and not (set(component) & entries):
                # 모든 노드가 디버그 노이즈 (comment) 면 스킵
                titles = [node_by_id[c].get("title", "") for c in component]
                islands.append([
                    f"{c} [{node_by_id[c].get('class','?')}] {node_by_id[c].get('title','')}" for c in component
                ])

        if computed_dropped or knot_runs or islands:
            results[gname] = {
                "computed_dropped": computed_dropped,
                "knot_runs": knot_runs,
                "islands": islands,
            }

    # ── 리포트 ───────────────────────────────────────────────────────────
    L = ["# PC_01_ABP 불필요 노드 확장 탐지", ""]
    total_cd = sum(len(r["computed_dropped"]) for r in results.values())
    total_kc = sum(len(r["knot_runs"]) for r in results.values())
    total_is = sum(len(r["islands"]) for r in results.values())
    L.append(f"- computed_dropped (결과 버려짐): {total_cd}")
    L.append(f"- knot_chain (3+ 직렬 reroute): {total_kc}")
    L.append(f"- orphan_island (2+ 노드 단절 군집): {total_is}")
    L.append("")

    L.append("## 1. computed_dropped — 실행되지만 결과 버려짐")
    L.append("")
    L.append("> exec 흐름에는 들어가는데 데이터 출력이 어디에도 안 감. side_effect_hint=True 면")
    L.append("> Set/Spawn/Apply 등 부작용 호출일 가능성(정상). False 면 정말 죽은 계산.")
    L.append("")
    for g, r in results.items():
        if not r["computed_dropped"]:
            continue
        L.append(f"### {g} — {len(r['computed_dropped'])}건")
        for c in r["computed_dropped"]:
            tag = "🟡 side-effect 가능" if c["side_effect_hint"] else "🔴 dead 계산"
            label = c["title"] if c["class"] != "K2Node_CallFunction" else f"{c['title']} (func={c['func']})"
            L.append(f"- {tag}  `{c['id']}` [{c['class']}] {label}  pos={c['pos']}  dropped={c['outputs_dropped']}")
        L.append("")

    L.append("## 2. knot_chain — 3개 이상 직렬 reroute")
    L.append("")
    L.append("> 정리하면 그래프 가독성↑. 동작엔 영향 없음.")
    L.append("")
    for g, r in results.items():
        if not r["knot_runs"]:
            continue
        L.append(f"### {g} — {len(r['knot_runs'])}개 체인")
        for chain in r["knot_runs"]:
            L.append(f"- {len(chain)}개: {' → '.join(chain)}")
        L.append("")

    L.append("## 3. orphan_island — 단절된 노드 군집 (2개 이상)")
    L.append("")
    L.append("> Entry/Event 노드에 도달 불가능. 통째 dead.")
    L.append("")
    for g, r in results.items():
        if not r["islands"]:
            continue
        L.append(f"### {g} — {len(r['islands'])}개 island")
        for isl in r["islands"]:
            L.append(f"- 노드 {len(isl)}개:")
            for s in isl:
                L.append(f"  - {s}")
        L.append("")

    out_path = os.path.join(DUMP_DIR, "redundant.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    print(f"== redundant 탐지 ==")
    print(f"computed_dropped: {total_cd}")
    print(f"knot_chain:       {total_kc}")
    print(f"orphan_island:    {total_is}")
    print(f"리포트: {out_path}")
    print()
    # stdout 요약
    print("[computed_dropped — 🔴 dead 계산만]")
    for g, r in results.items():
        for c in r["computed_dropped"]:
            if not c["side_effect_hint"]:
                label = c["title"] if c["class"] != "K2Node_CallFunction" else f"{c['title']} (func={c['func']})"
                print(f"  {g}: {c['id']} {label} pos={c['pos']} dropped={c['outputs_dropped']}")
    print()
    print("[computed_dropped — 🟡 side-effect 가능 (판단요)]")
    for g, r in results.items():
        for c in r["computed_dropped"]:
            if c["side_effect_hint"]:
                label = c["title"] if c["class"] != "K2Node_CallFunction" else f"{c['title']} (func={c['func']})"
                print(f"  {g}: {c['id']} {label} pos={c['pos']}")
    print()
    print("[knot_chain]")
    for g, r in results.items():
        for chain in r["knot_runs"]:
            print(f"  {g}: {len(chain)}개 {chain[0]}..{chain[-1]}")
    print()
    print("[orphan_island]")
    for g, r in results.items():
        for isl in r["islands"]:
            print(f"  {g}: {len(isl)}개 노드 — {isl[0]} ...")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
