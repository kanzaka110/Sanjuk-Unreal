#!/usr/bin/env python3
"""scripts/**/*.py 를 grep해 Monolith 액션 사용 카운트를 산출.

전략:
  1) action_catalog.json 로드 → 도메인별 액션 리스트
  2) scripts/*.py 텍스트에서 두 패턴 매칭
       a) `rpc("<action>", ...)`           # helper 호출 패턴 (가장 흔함)
       b) `"action": "<action>"`           # raw body 패턴
       c) `<namespace>_query(...)`         # 직접 도메인 콜 (드묾)
  3) 도메인 컨텍스트: 동일 파일에서 가장 빈도 높은 *_query 이름을 도메인으로 추정.
     없으면 unknown 으로 두고 후처리에서 액션 이름 기반으로 best-match.

출력:
  .claude/state/action_usage.json  ─ {"by_domain": {ns: [actions...]}, "by_action": {action: [files...]}}
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
STATE_DIR = os.path.join(REPO_ROOT, ".claude", "state")
CATALOG_PATH = os.path.join(STATE_DIR, "action_catalog.json")
USAGE_PATH = os.path.join(STATE_DIR, "action_usage.json")

NS_PATTERN = re.compile(r'"name"\s*:\s*"([a-z_]+_query|monolith_\w+)"')
# helper-name-agnostic: `something("snake_case_id", ...)` 모두 캡처해서
# 카탈로그 액션 리스트와 정확 매칭한다.
HELPER_CALL_PATTERN = re.compile(r'[A-Za-z_][\w]*\(\s*["\']([a-z][a-z0-9_]*)["\']')
ACTION_PATTERN = re.compile(r'"action"\s*:\s*"([a-z_][a-z0-9_]*)"')
DIRECT_CALL_PATTERN = re.compile(
    r'\b([a-z_]+_query)\(\s*["\']([a-z_]+)["\']'
)


def load_catalog() -> dict:
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def detect_domain_context(text: str) -> str | None:
    """파일 텍스트에서 가장 자주 등장하는 namespace 이름 반환."""
    counter: dict[str, int] = defaultdict(int)
    for m in NS_PATTERN.finditer(text):
        ns = m.group(1)
        if ns.endswith("_query"):
            ns = ns[: -len("_query")]
        elif ns.startswith("monolith_"):
            ns = "monolith"
        counter[ns] += 1
    if not counter:
        return None
    return max(counter, key=counter.get)


def collect_actions(text: str, known: set[str]) -> set[str]:
    """known(=catalog 전체 액션) 에 존재하는 토큰만 인정."""
    found = set()
    for m in HELPER_CALL_PATTERN.finditer(text):
        tok = m.group(1)
        if tok in known:
            found.add(tok)
    for m in ACTION_PATTERN.finditer(text):
        tok = m.group(1)
        if tok in known:
            found.add(tok)
    for m in DIRECT_CALL_PATTERN.finditer(text):
        tok = m.group(2)
        if tok in known:
            found.add(tok)
    return found


def main() -> int:
    catalog = load_catalog()
    domains: dict[str, list[str]] = {
        name: info["actions"] for name, info in catalog["domains"].items()
    }
    # action -> 가능한 도메인 후보 (정확 매칭용)
    action_to_domains: dict[str, list[str]] = defaultdict(list)
    for ns, actions in domains.items():
        for a in actions:
            action_to_domains[a].append(ns)
    known_actions: set[str] = set(action_to_domains.keys())

    by_domain: dict[str, set[str]] = defaultdict(set)
    by_action: dict[str, set[str]] = defaultdict(set)
    files_scanned = 0
    files_with_hits = 0

    for root, _dirs, files in os.walk(os.path.join(REPO_ROOT, "scripts")):
        for fn in files:
            if not fn.endswith(".py"):
                continue
            fp = os.path.join(root, fn)
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            files_scanned += 1
            ctx = detect_domain_context(text)
            actions = collect_actions(text, known_actions)
            if not actions:
                continue
            files_with_hits += 1
            rel = os.path.relpath(fp, REPO_ROOT).replace("\\", "/")
            for a in actions:
                candidates = action_to_domains.get(a, [])
                # 액션이 카탈로그에 없으면 스킵 (다른 함수 이름 오탐 방지)
                if not candidates:
                    continue
                # 도메인 결정: 컨텍스트 일치 우선, 아니면 유일 후보, 마지막은 첫 후보
                if ctx and ctx in candidates:
                    chosen = ctx
                elif len(candidates) == 1:
                    chosen = candidates[0]
                else:
                    # 여러 도메인에 동일 이름 존재 — 컨텍스트 우선했지만 미일치
                    chosen = candidates[0]
                by_domain[chosen].add(a)
                by_action[a].add(rel)

    # 직렬화
    out = {
        "_meta": {
            "catalog_total": catalog["_meta"]["total_actions"],
            "files_scanned": files_scanned,
            "files_with_hits": files_with_hits,
            "used_actions_total": sum(len(v) for v in by_domain.values()),
        },
        "by_domain": {k: sorted(v) for k, v in by_domain.items()},
        "by_action": {k: sorted(v) for k, v in by_action.items()},
    }
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(USAGE_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"Wrote {USAGE_PATH}")
    print(f"  files_scanned   = {files_scanned}")
    print(f"  files_with_hits = {files_with_hits}")
    print(f"  used_actions    = {out['_meta']['used_actions_total']}")
    print()
    print("Per-domain usage:")
    for ns in sorted(domains):
        total = len(domains[ns])
        used = len(by_domain.get(ns, set()))
        print(f"  {ns:20s} {used:4d}/{total:4d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
