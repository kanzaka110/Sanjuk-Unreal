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


def generate_body(
    category: str,
    facts: str,
    trend_context: str = "",
    target_version: str | None = None,
) -> str:
    """핵심 사실 + 트렌드 컨텍스트로 Notion 본문 마크다운 생성 (opus)."""
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

    prompt = f"""UE 애니메이션 전문 교육자로서 아래 사실을 Notion 마크다운 본문으로 작성하세요.{ver_note}

## 핵심 사실
{facts[:6000]}
{trend_section}
⚠️ URL은 핵심 사실에 있는 것만 사용. 추측 금지.

## 형식
# 📖 {category} 상세 정리
## {category}란? (4~6문장 + > 💡 핵심 가치 인용구)
---
## 주요 활용 분야 (표: 분야|설명|예시)
---
## 핵심 구조 (표: 요소|역할|비고 + 작동 원리)
---
## UE 5.x 업데이트 (### 🔷 주요 기능별 4~6문장)
---
## 비교표 (표: 기법|특징|용도|성능)
---
# 🎬 영상 목록 (표: 제목|출처|링크|시간, 최소 5개)
---
# 🛠️ 단계별 가이드 (STEP 1~4+, UI 경로 포함)
---
# 🔗 연관 자료 (링크 리스트)
---
규칙: 마크다운 테이블, ```코드```, ---구분, >팁, **굵게**, 한국어, 🆕는 1주 내 신규만"""

    return claude_cli(prompt, model="sonnet", timeout=300, effort="max") or ""


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
