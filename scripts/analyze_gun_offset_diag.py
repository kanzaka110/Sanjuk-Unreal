#!/usr/bin/env python3
"""PC_01_ABP Gun 모드 통돌이 원인 분리 — read-only 정적 진단 (v2: id/connections 수정)."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Any

ASSET = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
ENDPOINT = "http://localhost:9316/mcp"
CACHE = Path(__file__).parent / "backups" / "pc01_abp_animgraph_2026-06-12.t3d"


def rpc(name: str, action: str, params: dict[str, Any]) -> Any:
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": name, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(ENDPOINT, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        d = json.loads(resp.read().decode("utf-8"))
    res = d.get("result", {})
    if res.get("isError"):
        return {"ERROR": res["content"][0]["text"][:400]}
    txt = res["content"][0]["text"]
    try:
        return json.loads(txt)
    except Exception:
        return txt


def load_graph(gname: str) -> dict | None:
    if gname == "AnimGraph" and CACHE.exists():
        return json.loads(CACHE.read_text(encoding="utf-8"))
    g = rpc("blueprint_query", "export_graph", {"asset_path": ASSET, "graph_name": gname})
    if isinstance(g, dict) and "ERROR" not in g and g.get("nodes"):
        return g
    return None


def nodemap(g: dict) -> dict[str, dict]:
    return {n["id"]: n for n in g.get("nodes", [])}


def trace_back(g: dict, to_node: str, to_pin: str, depth=0, seen=None) -> None:
    """connections 리스트로 입력 소스 역추적 (데이터 핀 위주)."""
    if seen is None:
        seen = set()
    nm = nodemap(g)
    conns = g.get("connections", [])
    ind = "  " * depth
    feeders = [c for c in conns if c["to_node"] == to_node and (to_pin == "" or c["to_pin"] == to_pin)]
    for c in feeders:
        src, sp = c["from_node"], c["from_pin"]
        scls = nm.get(src, {}).get("class", "?")
        stitle = (nm.get(src, {}).get("title", "") or "").replace("\n", " ")[:40]
        print(f"{ind}<= {src}.{sp}  [{scls}] {stitle}")
        if (src, sp) in seen or depth > 7:
            continue
        seen.add((src, sp))
        # 위로: 해당 노드의 모든 입력 데이터핀
        trace_back(g, src, "", depth + 1, seen)


def main() -> None:
    print("#" * 70)
    print("# A. OffsetRootBone 노드 전수 + 핀 상태")
    print("#" * 70)
    ag = load_graph("AnimGraph")
    nm = nodemap(ag)
    orb = [n for n in ag["nodes"] if "OffsetRootBone" in n.get("class", "")]
    print(f"OffsetRootBone {len(orb)}개 / AnimGraph 총 {len(ag['nodes'])}노드\n")
    for n in orb:
        print(f"· {n['id']}  (title={n.get('title','').splitlines()[0] if n.get('title') else ''})")
        for p in n.get("pins", []):
            if p["name"] in ("RotationMode", "TranslationMode", "bResetEveryFrame", "MaxRotationError"):
                print(f"    {p['name']}: default={p.get('default_value')!r} connected_to={p.get('connected_to')}")

    print("\n" + "#" * 70)
    print("# B. bResetEveryFrame reset 소스 전체 역추적 (OR 입력)")
    print("#" * 70)
    for n in orb:
        print(f"\n{n['id']}.bResetEveryFrame 소스:")
        trace_back(ag, n["id"], "bResetEveryFrame", 1)

    print("\n" + "#" * 70)
    print("# C. AimOffset 입력 (재확인)")
    print("#" * 70)
    for n in ag["nodes"]:
        if "RotationOffsetBlendSpace" in n.get("class", ""):
            for p in n.get("pins", []):
                if p["name"] in ("X", "Y", "bAlphaBoolEnabled"):
                    print(f"  {p['name']}: {p.get('connected_to')}")

    print("\n" + "#" * 70)
    print("# D. AimYaw/AimPitch/ResetOffset SET 위치 탐색")
    print("#" * 70)
    graphs = rpc("blueprint_query", "list_graphs", {"asset_path": ASSET})
    glist = []
    if isinstance(graphs, dict):
        glist = graphs.get("graphs") or graphs.get("names") or []
    elif isinstance(graphs, list):
        glist = graphs
    print(f"그래프 목록: {[g if isinstance(g,str) else g.get('name') for g in glist][:40]}\n")
    for gentry in glist:
        gname = gentry if isinstance(gentry, str) else gentry.get("name", "")
        if not gname:
            continue
        g = load_graph(gname)
        if not g:
            continue
        hits = []
        for n in g["nodes"]:
            blob = json.dumps(n).lower()
            if ("variableset" in n.get("class", "").lower() and
                    any(k in blob for k in ["aimyaw", "aimpitch", "resetoffset"])):
                # SET 노드
                var = next((p["name"] for p in n["pins"] if p["name"] in ("AimYaw", "AimPitch", "ResetOffset")), "?")
                hits.append((n["id"], var))
            if "normalizeddelta" in blob and "baseaimrotation" in blob:
                hits.append((n["id"], "AimDelta계산?"))
        if hits:
            print(f"[그래프 {gname}] ({len(g['nodes'])}노드)")
            for hid, hv in hits:
                print(f"    {hid}  -> {hv}")
                # AimYaw set이면 그 입력 역추적 (기준 RootTransform vs CharacterTransform)
                if hv in ("AimYaw", "AimPitch"):
                    trace_back(g, hid, "", 2)

    print("\n" + "#" * 70)
    print("# E. GetOffsetRootRotationMode 분기 (이미 Accumulate 반환 가능?)")
    print("#" * 70)
    fg = load_graph("GetOffsetRootRotationMode")
    if fg:
        fnm = nodemap(fg)
        for n in fg["nodes"]:
            if "FunctionResult" in n.get("class", ""):
                rv = next((p.get("default_value") for p in n["pins"] if p["name"] == "ReturnValue"), "?")
                ein = next((p.get("connected_to") for p in n["pins"] if p["name"] == "execute"), None)
                print(f"  {n['id']}: ReturnValue={rv!r}  execute<={ein}")
        print("  조건 노드(PropertyAccess/Commutative):")
        for n in fg["nodes"]:
            if "PropertyAccess" in n.get("class", "") or "Commutative" in n.get("class", ""):
                t = (n.get("title", "") or "").replace("\n", " ")[:60]
                print(f"    {n['id']} [{n['class']}] {t}")


main()
