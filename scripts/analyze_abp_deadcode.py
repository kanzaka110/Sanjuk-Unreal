#!/usr/bin/env python3
"""PC_01_ABP 미사용(dead) 변수/함수/노드 탐지.

기준 (사용자 합의):
  - DrawDebug / AnimRewindRecorderEmit 그래프에서만 참조되는 변수·함수 = "디버그 전용 = 미사용".
  - 어느 그래프에서도 참조 없는 변수 = "그래프 참조 0" (단, Chooser 컬럼 / SM transition rule /
    C++ PropertyAccess / AnimGraph 핀 바인딩은 Monolith로 안 보여 오탐 가능 → 캐비엇 표기).
  - orphan 노드 = 모든 핀의 connected_to 가 비어 있는 노드 (롤백 잔해 후보, 가장 안전한 판정).

출력: dumps/deadcode/ 에 그래프별 raw dump + report.md.
컨텍스트 절약을 위해 stdout 에는 요약만 출력.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from monolith_helpers import MonolithClient  # noqa: E402

ASSET = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
DEBUG_GRAPHS = {"DrawDebug", "AnimRewindRecorderEmit"}
# CallFunction 으로 호출되지 않고 '바인딩'으로 쓰이는 함수 패턴 (오탐 방지).
BINDING_PREFIXES = ("OnStateEntry_", "OnUpdate_", "OnState")
# AnimGraph / ThreadSafe 평가 경로로 엔진이 직접 호출하는 함수 (CallFunction 안 나타남).
BINDING_FUNCS = {
    "BlueprintThreadSafeUpdateAnimation",
    "UpdateValueFromPostEvaluation",
    "AnimGraph",
    "EventGraph",
}

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dumps", "deadcode")


def extract_var_name(node: dict) -> str | None:
    """K2Node_VariableGet/Set 노드 → 변수명. title 'Get X'/'Set X' 파싱."""
    title = str(node.get("title", ""))
    for pre in ("Get ", "Set "):
        if title.startswith(pre):
            name = title[len(pre):]
            for suf in (" (a copy)", " (Copy)"):
                if name.endswith(suf):
                    name = name[: -len(suf)]
            return name.strip()
    return None


def node_is_orphan(node: dict) -> bool:
    """모든 핀이 비연결이면 orphan. 핀 없는 노드(코멘트 등)는 제외."""
    pins = node.get("pins") or []
    if not pins:
        return False
    for p in pins:
        if p.get("connected_to"):
            return False
    return True


def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)
    cli = MonolithClient(ASSET)

    graphs = cli.bp("list_graphs")["graphs"]
    graph_names = {g["name"] for g in graphs}
    variables = cli.get_variables().get("variables", [])
    var_names = {v.get("name") for v in variables if isinstance(v, dict)}

    # 참조 인덱스: var -> {real:set(graph), debug:set(graph)}
    var_refs: dict[str, dict[str, set]] = {v: {"real": set(), "debug": set()} for v in var_names}
    func_refs: dict[str, dict[str, set]] = {f: {"real": set(), "debug": set()} for f in graph_names}
    orphans: dict[str, list[str]] = {}

    for g in graphs:
        gname = g["name"]
        is_debug = gname in DEBUG_GRAPHS
        try:
            data = cli.get_graph_data(gname)
        except Exception as exc:  # noqa: BLE001
            print(f"  ! {gname}: {exc}")
            continue
        with open(os.path.join(OUT_DIR, f"{gname.replace(' ', '_')}.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)

        nodes = data.get("nodes", [])
        bucket = "debug" if is_debug else "real"
        g_orphans = []
        for n in nodes:
            cls = str(n.get("class", ""))
            if cls in ("K2Node_VariableGet", "K2Node_VariableSet"):
                vn = extract_var_name(n)
                if vn in var_refs:
                    var_refs[vn][bucket].add(gname)
            elif cls == "K2Node_CallFunction":
                fn = n.get("function")
                if fn in func_refs:
                    func_refs[fn][bucket].add(gname)
            # orphan 검사 (디버그 그래프는 노이즈라 제외)
            if not is_debug and node_is_orphan(n):
                g_orphans.append(f"{n.get('id')} [{cls}] {n.get('title','')}")
        if g_orphans:
            orphans[gname] = g_orphans

    # ── 변수 분류 ────────────────────────────────────────────────────────
    used, debug_only, no_ref = [], [], []
    for v in sorted(var_names):
        r = var_refs[v]
        if r["real"]:
            used.append(v)
        elif r["debug"]:
            debug_only.append((v, sorted(r["debug"])))
        else:
            no_ref.append(v)

    # ── 함수 분류 ────────────────────────────────────────────────────────
    f_used, f_debug_only, f_uncalled = [], [], []
    for fn in sorted(graph_names):
        if fn in DEBUG_GRAPHS or fn in BINDING_FUNCS or fn.startswith(BINDING_PREFIXES):
            continue  # 바인딩/디버그 그래프 자체는 호출분석 대상 아님
        r = func_refs[fn]
        if r["real"]:
            f_used.append(fn)
        elif r["debug"]:
            f_debug_only.append((fn, sorted(r["debug"])))
        else:
            f_uncalled.append(fn)

    # ── 리포트 ───────────────────────────────────────────────────────────
    L = ["# PC_01_ABP 미사용 후보 리포트", ""]
    L.append(f"- asset: `{ASSET}`")
    L.append(f"- 변수 {len(var_names)} / 그래프 {len(graph_names)} / 디버그그래프 {sorted(DEBUG_GRAPHS)}")
    L.append("")
    L.append("> ⚠ 오탐 주의: 변수는 **Chooser 컬럼 / SM transition rule 서브그래프 / C++ PropertyAccess /")
    L.append("> AnimGraph 핀 바인딩**으로도 소비될 수 있으나 Monolith 로는 안 보임. '그래프 참조 0' 은")
    L.append("> 반드시 에디터 우클릭 'Find References' 로 교차확인 후 삭제.")
    L.append("")

    L.append(f"## 1. 디버그 전용 변수 — {len(debug_only)}개 (실사용 없음, 안전도 中)")
    L.append("> DrawDebug / AnimRewindRecorderEmit 에서만 Get/Set. 제거 시 디버그 로그만 영향.")
    L.append("")
    for v, gs in debug_only:
        L.append(f"- `{v}` — {', '.join(gs)}")
    L.append("")

    L.append(f"## 2. 그래프 참조 0 변수 — {len(no_ref)}개 (오탐 가능, Find References 필수)")
    L.append("")
    for v in no_ref:
        L.append(f"- `{v}`")
    L.append("")

    L.append(f"## 3. orphan 노드 (롤백 잔해, 안전도 高) — {sum(len(x) for x in orphans.values())}개")
    L.append("> 모든 핀 비연결. 비-디버그 그래프만. 제거해도 동작 무영향.")
    L.append("")
    for gname, lst in orphans.items():
        L.append(f"### {gname} — {len(lst)}개")
        for s in lst:
            L.append(f"- {s}")
        L.append("")

    L.append(f"## 4. 디버그 전용 함수 — {len(f_debug_only)}개")
    L.append("")
    for fn, gs in f_debug_only:
        L.append(f"- `{fn}` — {', '.join(gs)}")
    L.append("")

    L.append(f"## 5. 호출 안 되는 함수 — {len(f_uncalled)}개 (바인딩 함수 제외, 오탐 가능)")
    L.append("> CallFunction 으로 안 불림. 단 AnimGraph 노드/SM 바인딩/인터페이스일 수 있어 교차확인 필수.")
    L.append("")
    for fn in f_uncalled:
        L.append(f"- `{fn}`")
    L.append("")

    report_path = os.path.join(OUT_DIR, "report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    # stdout 요약
    print(f"== PC_01_ABP dead-code 분석 ==")
    print(f"변수 {len(var_names)}: 사용 {len(used)} / 디버그전용 {len(debug_only)} / 참조0 {len(no_ref)}")
    print(f"함수: 디버그전용 {len(f_debug_only)} / 미호출 {len(f_uncalled)}")
    print(f"orphan 노드: {sum(len(x) for x in orphans.values())}개 (그래프 {len(orphans)}개)")
    print(f"리포트: {report_path}")
    print()
    print("[디버그 전용 변수]")
    for v, gs in debug_only:
        print(f"  {v}  <- {','.join(gs)}")
    print("[그래프 참조 0 변수]")
    print("  " + ", ".join(no_ref))
    print("[orphan 노드]")
    for gname, lst in orphans.items():
        for s in lst:
            print(f"  {gname}: {s}")
    print("[디버그 전용 함수]")
    for fn, gs in f_debug_only:
        print(f"  {fn}  <- {','.join(gs)}")
    print("[미호출 함수]")
    print("  " + ", ".join(f_uncalled))
    return 0


if __name__ == "__main__":
    sys.exit(main())
