"""STEP 1-2: 다중소스 검색 + 품질 검증 + 조건부 재검색."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

from briefing_config import CATEGORY_KEYWORDS, SEARCH_SOURCES

# UE 관련성 판별용 키워드 (하나라도 포함되면 관련 결과로 판정)
_UE_RELEVANCE_TERMS = frozenset({
    "unreal", "ue5", "ue4", "ue 5", "ue 4", "epic games", "언리얼",
    "blueprint", "블루프린트", "nanite", "lumen", "niagara", "metahuman",
    "sequencer", "control rig", "animation blueprint", "animgraph",
    "skeletal mesh", "morph target", "chaos", "fab.com", "fab marketplace",
})

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shared_config import claude_cli

try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None


# ─── 데이터 구조 ─────────────────────────────────────────────────────────────

@dataclass
class SourcedResult:
    """소스 출처가 추적되는 검색 결과."""
    title: str
    url: str
    snippet: str
    source_type: str  # "claude_web" | "ddgs"
    domain: str = ""

    def __post_init__(self):
        if not self.domain and self.url:
            try:
                from urllib.parse import urlparse
                self.domain = urlparse(self.url).netloc
            except Exception:
                self.domain = ""


@dataclass
class QualityScore:
    """검색 결과 품질 점수."""
    source_diversity: float = 0.0  # unique 도메인 수 / 기대 도메인 수
    relevance: float = 0.0        # snippet에 UE 키워드가 있는 결과 비율
    count: float = 0.0            # 총 결과 수 / 기대 최소 수
    overall: float = 0.0

    def compute(self, results: list[SourcedResult], expected_domains: int = 5, expected_count: int = 10):
        unique_domains = len({r.domain for r in results if r.domain})
        total = len(results)
        self.source_diversity = min(unique_domains / max(expected_domains, 1), 1.0)
        self.count = min(total / max(expected_count, 1), 1.0)
        # 관련성: snippet에 UE 키워드가 있는 비율
        if total > 0:
            relevant = sum(1 for r in results if _is_ue_relevant(r.title, r.snippet, r.url))
            self.relevance = relevant / total
        else:
            self.relevance = 0.0
        self.overall = (self.source_diversity * 0.3 + self.count * 0.3 + self.relevance * 0.4)
        return self


# ─── Claude CLI 웹검색 ────────────────────────────────────────────────────────

def search_claude_cli(category: str, queries: list[str]) -> list[SourcedResult]:
    """Claude CLI + WebSearch로 검색 후 SourcedResult 리스트 반환."""
    today_str = date.today().strftime("%Y-%m-%d")
    one_week_ago = (date.today() - timedelta(days=7)).strftime("%Y-%m-%d")

    # 카테고리 특화 키워드 활용
    keywords = CATEGORY_KEYWORDS.get(category, [category])
    keyword_hint = ", ".join(keywords[:4])

    search_prompt = f"""UE5 애니메이션 [{category}] 관련 최신 콘텐츠를 웹 검색으로 찾아주세요.

핵심 키워드: {keyword_hint}

검색어:
{chr(10).join(f'- {q}' for q in queries)}

검색 우선순위:
1. Epic Games 공식 블로그/문서/Unreal Fest/GDC 발표
2. YouTube (Alex Forsythe, Ryan Laley, Matt Aspland 등 UE 유튜버)
3. 80.lv, Reddit r/unrealengine 등 게임개발 커뮤니티
4. GitHub 오픈소스, Fab 마켓플레이스 신규 에셋/플러그인

각 결과를 아래 형식으로 정리:
RESULT_START
제목: (제목)
URL: (URL)
내용: (핵심 내용 2-3문장, [{category}]와 직접 관련된 내용만)
RESULT_END

{one_week_ago} 이후 게시된 콘텐츠 우선. 한국어+영어 모두 포함.
검색 결과에서 확인된 실제 URL만 포함. URL을 추측하지 말 것."""

    raw = claude_cli(search_prompt, model="sonnet", web_search=True, timeout=300)
    return _parse_claude_results(raw)


def _parse_claude_results(raw: str) -> list[SourcedResult]:
    """Claude CLI 응답에서 구조화된 결과를 파싱."""
    results: list[SourcedResult] = []
    if not raw:
        return results

    # 구조화된 RESULT_START/END 파싱 시도
    import re
    blocks = re.split(r"RESULT_START\s*\n?", raw)
    for block in blocks[1:]:
        end_idx = block.find("RESULT_END")
        if end_idx > 0:
            block = block[:end_idx]
        title_m = re.search(r"제목:\s*(.+)", block)
        url_m = re.search(r"URL:\s*(https?://\S+)", block)
        content_m = re.search(r"내용:\s*(.+?)(?:\n\n|\Z)", block, re.DOTALL)
        if title_m:
            results.append(SourcedResult(
                title=title_m.group(1).strip(),
                url=url_m.group(1).strip() if url_m else "",
                snippet=content_m.group(1).strip() if content_m else "",
                source_type="claude_web",
            ))

    # 구조화 파싱 실패 시 전체 텍스트를 하나의 결과로
    if not results and raw.strip():
        # URL 추출 시도
        urls = re.findall(r"https?://\S+", raw)
        seen_urls: set[str] = set()
        for url in urls:
            url = url.rstrip(")")
            if url not in seen_urls:
                seen_urls.add(url)
                results.append(SourcedResult(
                    title="",
                    url=url,
                    snippet="",
                    source_type="claude_web",
                ))
        # URL도 없으면 전체를 하나의 snippet으로
        if not results:
            results.append(SourcedResult(
                title="검색 결과",
                url="",
                snippet=raw[:5000],
                source_type="claude_web",
            ))

    return results


# ─── DuckDuckGo 보조 검색 ─────────────────────────────────────────────────────

# 보일러플레이트 패턴 (네비게이션, 로그인, 쿠키 등)
_BOILERPLATE_PATTERNS = (
    "sign in to", "log in to", "create an account",
    "cookie", "privacy policy", "terms of service",
    "home >", "home >", "breadcrumb",
    "skip to content", "skip to main",
    "subscribe to", "newsletter",
    "page not found", "404",
    "access denied", "forbidden",
)


def _is_ue_relevant(title: str, snippet: str, url: str) -> bool:
    """제목/snippet/URL에 UE 관련 키워드가 하나라도 있으면 True."""
    text = f"{title} {snippet} {url}".lower()
    return any(term in text for term in _UE_RELEVANCE_TERMS)


def _is_boilerplate(snippet: str) -> bool:
    """snippet이 보일러플레이트(네비게이션, 쿠키 등)인지 판별."""
    lower = snippet.lower()
    # 보일러플레이트 패턴 매칭
    if any(pat in lower for pat in _BOILERPLATE_PATTERNS):
        return True
    # snippet의 50% 이상이 '>' 구분자면 네비게이션 텍스트
    if lower.count(">") >= 3 and lower.count(">") / max(len(lower.split()), 1) > 0.3:
        return True
    return False


def search_ddgs(
    queries: list[str],
    max_results_per_query: int = 5,
    timelimit: str = "w",
) -> list[SourcedResult]:
    """DuckDuckGo로 보조 검색. timelimit: 'd'=1일, 'w'=1주, 'm'=1달."""
    if DDGS is None:
        return []
    results: list[SourcedResult] = []
    seen_urls: set[str] = set()
    filtered = 0

    for query in queries:
        try:
            ddgs = DDGS()
            for r in ddgs.text(query, timelimit=timelimit, max_results=max_results_per_query):
                url = r.get("href", "")
                title = r.get("title", "")
                snippet = r.get("body", "")
                if not url or url in seen_urls:
                    continue
                # 관련성 필터: UE 무관 결과 제거
                if not _is_ue_relevant(title, snippet, url):
                    filtered += 1
                    continue
                # 빈/짧은 snippet 제거 (10자 미만이면 사실 추출에 무의미)
                if len(snippet) < 10:
                    filtered += 1
                    continue
                # 보일러플레이트 필터: 네비게이션/쿠키/로그인 텍스트 제거
                if _is_boilerplate(snippet):
                    filtered += 1
                    continue
                seen_urls.add(url)
                results.append(SourcedResult(
                    title=title,
                    url=url,
                    snippet=snippet,
                    source_type="ddgs",
                ))
        except Exception as e:
            print(f"  ⚠️ DDGS 검색 실패 ({query[:30]}...): {e}")
            continue

    if filtered:
        print(f"    DDGS 필터링: {filtered}건 제외 (무관/빈 snippet)")
    return results


# ─── DuckDuckGo 뉴스 검색 ────────────────────────────────────────────────────

def search_ddgs_news(
    queries: list[str],
    max_results_per_query: int = 3,
    timelimit: str = "w",
) -> list[SourcedResult]:
    """DuckDuckGo 뉴스 API로 검색. 게시 날짜 메타데이터 포함."""
    if DDGS is None:
        return []
    results: list[SourcedResult] = []
    seen_urls: set[str] = set()
    filtered = 0

    for query in queries[:5]:
        try:
            ddgs = DDGS()
            for r in ddgs.news(query, timelimit=timelimit, max_results=max_results_per_query):
                url = r.get("url", "")
                title = r.get("title", "")
                snippet = r.get("body", "")
                pub_date = r.get("date", "")
                if not url or url in seen_urls:
                    continue
                if not _is_ue_relevant(title, snippet, url):
                    filtered += 1
                    continue
                if len(snippet) < 10:
                    filtered += 1
                    continue
                seen_urls.add(url)
                # 날짜 정보를 snippet에 포함 (사실 추출 시 신선도 판단용)
                dated_snippet = f"[{pub_date}] {snippet}" if pub_date else snippet
                results.append(SourcedResult(
                    title=title,
                    url=url,
                    snippet=dated_snippet,
                    source_type="ddgs_news",
                ))
        except Exception as e:
            print(f"  ⚠️ DDGS 뉴스 검색 실패 ({query[:30]}...): {e}")
            continue

    if filtered:
        print(f"    DDGS뉴스 필터링: {filtered}건 제외")
    return results


# ─── 다중소스 통합 검색 ───────────────────────────────────────────────────────

def build_queries(category: str) -> list[str]:
    """카테고리별 특화 키워드 기반으로 정밀 쿼리 생성."""
    keywords = CATEGORY_KEYWORDS.get(category, [category])

    # 1순위: 카테고리 특화 쿼리 (가장 정밀)
    queries: list[str] = []
    for kw in keywords[:3]:
        queries.append(f"UE5 {kw} new 2026")
        queries.append(f"Unreal Engine {kw} update")
    queries.append(f"언리얼 엔진 {category} 최신")
    queries.append(f"site:youtube.com UE5 {keywords[0]}")

    # 2순위: 소스별 쿼리 (커버리지 확보, 대표 키워드만)
    primary_kw = keywords[0]
    for source_queries in SEARCH_SOURCES.values():
        if source_queries:
            queries.append(f"{source_queries[0]} {primary_kw}")

    # 중복 제거하면서 순서 유지
    seen: set[str] = set()
    unique: list[str] = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            unique.append(q)

    return unique[:15]


def multi_source_search(category: str) -> list[SourcedResult]:
    """DDGS text+news 1차 검색 + Claude CLI 보완. 토큰 최적화."""
    queries = build_queries(category)

    # DDGS text 검색: 1주일 필터 (무료, 토큰 0)
    ddgs_results = search_ddgs(queries[:8], max_results_per_query=3, timelimit="w")
    ddgs_domains = len({r.domain for r in ddgs_results if r.domain})
    print(f"    DDGS text(1w): {len(ddgs_results)}건 ({ddgs_domains}개 도메인)")

    # DDGS news 검색: 날짜 메타데이터 포함 (무료, 토큰 0)
    news_results = search_ddgs_news(queries[:5], max_results_per_query=3, timelimit="w")
    seen = {r.url for r in ddgs_results if r.url}
    news_added = 0
    for r in news_results:
        if r.url and r.url not in seen:
            ddgs_results.append(r)
            seen.add(r.url)
            news_added += 1
    if news_added:
        print(f"    DDGS news(1w): +{news_added}건 추가")
    ddgs_domains = len({r.domain for r in ddgs_results if r.domain})

    # 니치 카테고리에서 결과 부족 시 → 1달로 확장 (토큰 0)
    if len(ddgs_results) < 5:
        extra = search_ddgs(queries[:6], max_results_per_query=3, timelimit="m")
        for r in extra:
            if r.url and r.url not in seen:
                ddgs_results.append(r)
                seen.add(r.url)
        ddgs_domains = len({r.domain for r in ddgs_results if r.domain})
        print(f"    DDGS(1m 보완): {len(ddgs_results)}건 ({ddgs_domains}개 도메인)")

    # DDGS 결과가 충분하고 다양하면 Claude CLI 스킵
    if len(ddgs_results) >= 15 and ddgs_domains >= 5:
        print(f"    Claude: 스킵 (DDGS 충분+다양)")
        return ddgs_results

    # Claude CLI 보완 검색 (DDGS 부족하거나 편향 시)
    # DDGS 건수에 따라 Claude 쿼리 수 조절 (토큰 절약)
    cli_query_count = 4 if len(ddgs_results) >= 10 else 6
    claude_results = search_claude_cli(category, queries[:cli_query_count])
    print(f"    Claude: {len(claude_results)}건 (쿼리 {cli_query_count}개)")

    # 병합 (URL 중복 제거)
    seen_urls: set[str] = set()
    merged: list[SourcedResult] = []
    for r in ddgs_results + claude_results:
        if r.url and r.url in seen_urls:
            continue
        if r.url:
            seen_urls.add(r.url)
        merged.append(r)

    return merged


# ─── 품질 검증 + 재검색 ──────────────────────────────────────────────────────

def assess_quality(results: list[SourcedResult]) -> QualityScore:
    """검색 결과의 품질 점수 산출."""
    score = QualityScore()
    score.compute(results)
    return score


def generate_supplementary_queries(category: str, existing_results: list[SourcedResult]) -> list[str]:
    """부족한 영역을 파악하고 보완 쿼리 생성."""
    existing_domains = {r.domain for r in existing_results if r.domain}
    missing_sources: list[str] = []

    target_domains = ["youtube.com", "github.com", "80.lv", "reddit.com", "unrealengine.com"]
    for d in target_domains:
        if not any(d in ed for ed in existing_domains):
            missing_sources.append(d)

    supplementary: list[str] = []
    for domain in missing_sources[:3]:
        supplementary.append(f"site:{domain} UE5 {category} animation 2026")

    return supplementary


def search_with_retry(category: str, max_rounds: int = 2) -> list[SourcedResult]:
    """품질 미달 시 자동 보완 검색. 최대 max_rounds 라운드."""
    results = multi_source_search(category)
    score = assess_quality(results)

    print(f"    품질: 다양성={score.source_diversity:.0%} 수량={score.count:.0%} 관련성={score.relevance:.0%} 종합={score.overall:.0%}")

    for round_num in range(1, max_rounds + 1):
        if score.overall >= 0.5:
            break
        print(f"    🔄 보완 검색 (라운드 {round_num})...")
        supplementary = generate_supplementary_queries(category, results)
        if not supplementary:
            break
        extra = search_ddgs(supplementary, max_results_per_query=3, timelimit="m")
        seen_urls = {r.url for r in results if r.url}
        for r in extra:
            if r.url and r.url not in seen_urls:
                results.append(r)
                seen_urls.add(r.url)
        score = assess_quality(results)
        print(f"    품질 (보완 후): 종합={score.overall:.0%}")

    return results


# 도메인 기반 소스 신뢰도 등급
_TRUST_TIERS: dict[str, str] = {
    "unrealengine.com": "★★★ Epic 공식",
    "dev.epicgames.com": "★★★ Epic 공식",
    "forums.unrealengine.com": "★★★ Epic 포럼",
    "www.unrealengine.com": "★★★ Epic 공식",
    "docs.unrealengine.com": "★★★ Epic 문서",
    "youtube.com": "★★☆ YouTube",
    "www.youtube.com": "★★☆ YouTube",
    "github.com": "★★☆ GitHub",
    "80.lv": "★★☆ 게임개발 미디어",
    "www.80.lv": "★★☆ 게임개발 미디어",
    "www.reddit.com": "★★☆ 커뮤니티",
    "reddit.com": "★★☆ 커뮤니티",
    "fab.com": "★★☆ Fab 마켓",
    "www.fab.com": "★★☆ Fab 마켓",
}


def _get_trust_tier(domain: str) -> str:
    """도메인의 신뢰도 등급을 반환."""
    return _TRUST_TIERS.get(domain, "★☆☆ 일반")


def results_to_text(results: list[SourcedResult]) -> str:
    """SourcedResult 리스트를 텍스트로 변환 (프롬프트용). 소스 신뢰도 태그 포함."""
    parts: list[str] = []
    for r in results:
        trust = _get_trust_tier(r.domain)
        lines = []
        lines.append(f"[{trust}]")
        if r.title:
            lines.append(f"제목: {r.title}")
        if r.url:
            lines.append(f"URL: {r.url}")
        if r.snippet:
            lines.append(f"내용: {r.snippet}")
        parts.append("\n".join(lines))
    return "\n---\n".join(parts)
