"""STEP 1-2: 다중소스 검색 + 품질 검증 + 조건부 재검색."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

from briefing_config import SEARCH_SOURCES

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
    freshness: float = 0.0        # 최신 콘텐츠 비율 (예상치)
    count: float = 0.0            # 총 결과 수 / 기대 최소 수
    overall: float = 0.0

    def compute(self, results: list[SourcedResult], expected_domains: int = 5, expected_count: int = 10):
        unique_domains = len({r.domain for r in results if r.domain})
        total = len(results)
        self.source_diversity = min(unique_domains / max(expected_domains, 1), 1.0)
        self.count = min(total / max(expected_count, 1), 1.0)
        self.freshness = 1.0 if total > 0 else 0.0  # Claude CLI가 최신 필터링 수행
        self.overall = (self.source_diversity * 0.4 + self.count * 0.4 + self.freshness * 0.2)
        return self


# ─── Claude CLI 웹검색 ────────────────────────────────────────────────────────

def search_claude_cli(category: str, queries: list[str]) -> list[SourcedResult]:
    """Claude CLI + WebSearch로 검색 후 SourcedResult 리스트 반환."""
    today_str = date.today().strftime("%Y-%m-%d")
    three_days_ago = (date.today() - timedelta(days=3)).strftime("%Y-%m-%d")
    date_range = f"after:{three_days_ago}"

    search_prompt = f"""다음 검색어들로 웹 검색을 수행하고, 언리얼 엔진 애니메이션 관련 최신 콘텐츠를 찾아주세요:

{chr(10).join(f'- {q} {date_range}' for q in queries)}

검색 범위:
- YouTube (UE 애니메이션 유튜버: Alex Forsythe, Ryan Laley, Matt Aspland 등)
- 80.lv, GameDev.net, Polycount 등 게임개발 커뮤니티
- Reddit r/unrealengine, Twitter/X
- Epic Games 공식 블로그, Unreal Fest/GDC 발표
- Fab 마켓플레이스 신규 애니메이션 에셋/플러그인
- GitHub 오픈소스 프로젝트

각 검색 결과를 아래 형식으로 정리해주세요:
RESULT_START
제목: (제목)
URL: (URL)
내용: (핵심 내용 2-3문장)
RESULT_END

최근 3일 내 올라온 콘텐츠 우선. 한국어와 영어 결과 모두 포함.
검색 결과에서 확인된 실제 URL만 포함."""

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

def search_ddgs(queries: list[str], max_results_per_query: int = 5) -> list[SourcedResult]:
    """DuckDuckGo로 보조 검색. 실패 시 빈 리스트 반환."""
    if DDGS is None:
        return []
    results: list[SourcedResult] = []
    seen_urls: set[str] = set()

    for query in queries:
        try:
            ddgs = DDGS()
            for r in ddgs.text(query, max_results=max_results_per_query):
                url = r.get("href", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    results.append(SourcedResult(
                        title=r.get("title", ""),
                        url=url,
                        snippet=r.get("body", ""),
                        source_type="ddgs",
                    ))
        except Exception as e:
            print(f"  ⚠️ DDGS 검색 실패 ({query[:30]}...): {e}")
            continue

    return results


# ─── 다중소스 통합 검색 ───────────────────────────────────────────────────────

def build_queries(category: str) -> list[str]:
    """카테고리에 맞는 8-12개 검색 쿼리 생성."""
    today_str = date.today().strftime("%Y-%m-%d")
    three_days_ago = (date.today() - timedelta(days=3)).strftime("%Y-%m-%d")
    date_range = f"after:{three_days_ago}"

    # 카테고리별 특화 쿼리
    queries = [
        f"Unreal Engine {category} latest news 2026",
        f"UE5 {category} tutorial new",
        f"언리얼 엔진 {category} 최신",
        f"site:youtube.com UE5 {category} animation",
    ]

    # 6개 소스 카테고리에서 쿼리 추가
    for source_queries in SEARCH_SOURCES.values():
        for sq in source_queries:
            queries.append(f"{sq} {category} 2026")

    # AI/GitHub 특화
    if category in ("AI Animation Tech", "GitHub/Open Source"):
        queries.extend([
            f"AI animation game development machine learning 2026",
            f"github UE5 animation AI new release 2026",
            f"neural animation motion diffusion model game",
        ])

    # 중복 제거하면서 순서 유지
    seen: set[str] = set()
    unique: list[str] = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            unique.append(q)

    return unique[:15]


def multi_source_search(category: str) -> list[SourcedResult]:
    """DDGS 1차 검색 + Claude CLI 보완. 토큰 최적화."""
    queries = build_queries(category)

    # DDGS 1차 검색 (무료, 토큰 0)
    ddgs_results = search_ddgs(queries[:8], max_results_per_query=3)
    print(f"    DDGS: {len(ddgs_results)}건")

    # DDGS 결과가 충분하면 Claude CLI 스킵
    if len(ddgs_results) >= 15:
        print(f"    Claude: 스킵 (DDGS 충분)")
        return ddgs_results

    # Claude CLI 보완 검색 (DDGS 부족 시)
    claude_results = search_claude_cli(category, queries[:6])
    print(f"    Claude: {len(claude_results)}건")

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

    print(f"    품질: 다양성={score.source_diversity:.0%} 수량={score.count:.0%} 종합={score.overall:.0%}")

    for round_num in range(1, max_rounds + 1):
        if score.overall >= 0.5:
            break
        print(f"    🔄 보완 검색 (라운드 {round_num})...")
        supplementary = generate_supplementary_queries(category, results)
        if not supplementary:
            break
        extra = search_ddgs(supplementary, max_results_per_query=3)
        seen_urls = {r.url for r in results if r.url}
        for r in extra:
            if r.url and r.url not in seen_urls:
                results.append(r)
                seen_urls.add(r.url)
        score = assess_quality(results)
        print(f"    품질 (보완 후): 종합={score.overall:.0%}")

    return results


def results_to_text(results: list[SourcedResult]) -> str:
    """SourcedResult 리스트를 텍스트로 변환 (프롬프트용)."""
    parts: list[str] = []
    for r in results:
        lines = []
        if r.title:
            lines.append(f"제목: {r.title}")
        if r.url:
            lines.append(f"URL: {r.url}")
        if r.snippet:
            lines.append(f"내용: {r.snippet}")
        lines.append(f"소스: {r.source_type} | 도메인: {r.domain}")
        parts.append("\n".join(lines))
    return "\n---\n".join(parts)
