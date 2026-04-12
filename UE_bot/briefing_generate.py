"""STEP 5: 메타데이터 추출 + 본문 생성 프롬프트."""

from __future__ import annotations

import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

from briefing_config import CATEGORIES, VALID_TAGS

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shared_config import claude_cli


def extract_json(text: str) -> dict | None:
    """텍스트에서 JSON 블록 추출."""
    m = re.search(r"```json\s*([\s\S]+?)\s*```", text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    for m in re.finditer(r"\{[\s\S]*\}", text):
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            continue
    return None


def generate_metadata(category: str, facts: str) -> dict:
    """핵심 사실에서 메타데이터 JSON 추출 (haiku)."""
    tag_list = ", ".join(VALID_TAGS)
    today = date.today().strftime("%Y년 %m월 %d일")
    since = (date.today() - timedelta(days=3)).strftime("%Y년 %m월 %d일")

    prompt = f"""아래 핵심 사실을 바탕으로 메타데이터만 JSON으로 추출하세요.

⚠️ 중요: 최근 3일({since}~{today}) 내 게시된 콘텐츠가 있는지 판단하세요.

핵심 사실:
{facts[:5000]}

⚠️ URL 규칙: 핵심 사실에 있는 URL만 사용. URL을 만들거나 추측하지 말 것.

반드시 아래 JSON만 출력하세요:
```json
{{
  "제목": "구체적이고 실용적인 한국어 제목",
  "요약": "8~12문장 상세 요약 (한국어)",
  "소스_링크": "핵심 사실에서 가장 관련 있는 URL",
  "난이도": "초급 또는 중급 또는 고급",
  "UE_버전": "5.5 또는 5.6 또는 5.7 또는 5.8+",
  "태그": ["태그1", "태그2"],
  "새_정보_여부": true 또는 false
}}
```
태그는 다음 중 1~3개만: {tag_list}"""

    result = claude_cli(prompt, model="haiku", timeout=120, effort="max")
    return extract_json(result) or {}


def _has_video_urls(facts: str) -> bool:
    """사실 텍스트에 영상 URL이 포함되어 있는지 확인."""
    video_indicators = ["youtube.com", "youtu.be", "vimeo.com", "twitch.tv"]
    facts_lower = facts.lower()
    return any(ind in facts_lower for ind in video_indicators)


def _extract_urls_from_facts(facts: str) -> list[str]:
    """사실 텍스트에서 모든 URL을 추출."""
    return re.findall(r"https?://\S+", facts)


def generate_body(
    category: str,
    facts: str,
    trend_context: str = "",
    target_version: str | None = None,
) -> str:
    """핵심 사실 + 트렌드 컨텍스트로 Notion 본문 마크다운 생성."""
    ver_note = (
        f"\n\n⚠️ **이 페이지는 UE {target_version} 버전 전용입니다.** "
        f"이 버전에서의 기능, 변경사항, 제한사항만 다루세요."
        if target_version else ""
    )

    trend_section = ""
    if trend_context and trend_context != "(이전 브리핑 데이터 없음 — 첫 실행)":
        trend_section = f"""
## 이전 대비 변화 분석
{trend_context[:2000]}
"""

    # ⑦ 영상 섹션: 사실에 영상 URL이 있을 때만 포함
    video_section = ""
    if _has_video_urls(facts):
        video_section = """
---
## 🎬 관련 영상
| 제목 | 출처 | 링크 | 길이 |
핵심 사실에 있는 영상 URL만 사용. URL이 없는 영상은 절대 추가하지 말 것."""

    prompt = f"""UE5 애니메이션 TA 교육 콘텐츠를 작성하세요.{ver_note}

## 입력 데이터 (핵심 사실)
{facts[:6000]}
{trend_section}
⚠️ URL은 위 데이터에 있는 것만 사용. 절대 추측/생성 금지.

## 출력 형식 (Notion 마크다운, 이 구조를 정확히 따를 것)

# 📖 {category} 상세 정리

## 개요
4~6문장으로 이 기술이 무엇이고 왜 중요한지 설명.
> 💡 한 줄 핵심 인사이트

---
## 주요 활용 분야
| 분야 | 설명 | 실제 예시 |
각 행에 구체적인 UE5 사용 사례를 기술.

---
## 핵심 구조
| 요소 | 역할 | 비고 |
기술의 아키텍처/구성요소를 표로 정리. 표 아래에 작동 원리 2~3문장 추가.

---
## UE 5.x 최신 업데이트
### 🔷 (기능명)
각 기능에 4~6문장. 버전 번호와 변경사항을 명확히.

---
## 기법 비교
| 기법 | 특징 | 용도 | 성능 영향 |
{video_section}
---
## 🛠️ 단계별 가이드
STEP 1~4+. 각 단계에 UE5 에디터 UI 경로 포함 (예: Edit > Project Settings > ...).

---
## 🔗 연관 자료
- 핵심 사실의 URL만 사용한 링크 리스트

---
규칙: 한국어, **굵게**, `코드`, 마크다운 테이블 활용. 🆕는 1주 내 신규만.
⚠️ 핵심 사실에 없는 URL을 절대 만들지 말 것. 없으면 해당 섹션을 비워두세요."""

    raw_body = claude_cli(prompt, model="sonnet", timeout=300, effort="max") or ""

    # ⑧ 생성 후 URL 검증: 입력 facts에 없는 URL 제거
    if raw_body:
        raw_body = _validate_urls(raw_body, facts)

    return raw_body


def _validate_urls(body: str, facts: str) -> str:
    """생성된 본문에서 입력 facts에 없는 URL을 제거."""
    fact_urls = set(_extract_urls_from_facts(facts))
    body_urls = set(_extract_urls_from_facts(body))

    # facts에 없는 URL = 환각
    hallucinated = body_urls - fact_urls
    if not hallucinated:
        return body

    cleaned = body
    for bad_url in hallucinated:
        # URL이 마크다운 링크 안에 있는 경우: [text](url) → text
        cleaned = re.sub(
            r"\[([^\]]*)\]\(" + re.escape(bad_url) + r"\)",
            r"\1",
            cleaned,
        )
        # 단독 URL인 경우 제거
        cleaned = cleaned.replace(bad_url, "")

    print(f"  🔍 URL 검증: {len(hallucinated)}개 환각 URL 제거")
    return cleaned


def make_fallback(category: str, facts: str) -> dict:
    """생성 실패 시 폴백 데이터."""
    return {
        "제목": f"{category} 브리핑 — {date.today().strftime('%Y.%m.%d')}",
        "요약": facts[:600].strip(),
        "소스_링크": "https://dev.epicgames.com/documentation/ko-kr/unreal-engine",
        "난이도": "중급",
        "UE_버전": "5.7",
        "태그": [],
        "새_정보_여부": False,
    }
