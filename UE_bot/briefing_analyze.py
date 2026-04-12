"""STEP 3-4: 청킹 + 핵심사실 추출 (Map-Reduce) + 교차 분석 + 트렌드 비교."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shared_config import claude_cli


# ─── STEP 3: Map-Reduce (데이터 절삭 해결) ────────────────────────────────────

def chunk_text(text: str, max_chars: int = 5000) -> list[str]:
    """텍스트를 의미 단위로 청크 분할. 기본 5000자 (호출 횟수 최소화)."""
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for line in text.split("\n"):
        line_len = len(line) + 1
        if current_len + line_len > max_chars and current:
            chunks.append("\n".join(current))
            current = [line]
            current_len = line_len
        else:
            current.append(line)
            current_len += line_len

    if current:
        chunks.append("\n".join(current))

    return chunks


def extract_facts(chunk: str, category: str) -> list[str]:
    """청크에서 핵심 사실을 추출 (haiku, map 단계)."""
    prompt = f"""아래 텍스트에서 UE5 애니메이션 관련 **핵심 사실**만 추출하세요.
카테고리: {category}

텍스트:
{chunk}

규칙:
- 각 사실은 한 줄로 작성 (번호 없이)
- 구체적 사실만 (버전 번호, 기능명, 도구명, URL 포함)
- "~라고 한다" 같은 불확실한 표현 제거
- 최소 5개, 최대 15개
- URL이 있으면 반드시 포함

FACT:로 시작하는 줄만 출력하세요."""

    result = claude_cli(prompt, model="haiku", timeout=60)
    if not result:
        return []

    facts: list[str] = []
    for line in result.split("\n"):
        line = line.strip()
        if line.startswith("FACT:"):
            fact = line[5:].strip()
            if fact:
                facts.append(fact)
        elif line and not line.startswith("#") and len(line) > 20:
            # FACT: 접두사 없이 사실만 나열한 경우도 수용
            facts.append(line)

    return facts


def map_reduce_extract(raw_text: str, category: str) -> str:
    """Map-Reduce로 전체 텍스트에서 핵심 사실 추출 (절삭 없음).

    1. raw_text를 ~3000자 청크로 분할
    2. 각 청크에서 haiku로 사실 추출 (map)
    3. 중복 제거 후 병합 (reduce)
    """
    chunks = chunk_text(raw_text, max_chars=3000)
    print(f"    청크: {len(chunks)}개")

    all_facts: list[str] = []
    for i, chunk in enumerate(chunks):
        facts = extract_facts(chunk, category)
        print(f"    청크 {i+1}/{len(chunks)}: {len(facts)}개 사실 추출")
        all_facts.extend(facts)

    # 중복 제거 (정확히 같은 문장)
    seen: set[str] = set()
    unique_facts: list[str] = []
    for f in all_facts:
        normalized = f.lower().strip()
        if normalized not in seen:
            seen.add(normalized)
            unique_facts.append(f)

    print(f"    총 사실: {len(unique_facts)}개 (중복 제거 후)")
    return "\n".join(unique_facts)


# ─── STEP 4: 교차 분석 + 트렌드 비교 ─────────────────────────────────────────

def analyze_trends(
    current_facts: str,
    category: str,
    previous_summaries: list[dict],
) -> str:
    """이전 브리핑과 비교하여 트렌드 분석. 이전 데이터 없으면 스킵."""
    # 같은 카테고리의 이전 브리핑만 필터
    prev_texts: list[str] = []
    for s in previous_summaries:
        if s.get("category") == category or not s.get("category"):
            text = f"{s.get('title', '')} | {s.get('summary', '')}"
            if text.strip(" |"):
                prev_texts.append(text)

    if not prev_texts:
        return ""  # CLI 호출 스킵

    prev_context = "\n".join(prev_texts[:10])

    prompt = f"""아래는 UE5 애니메이션 [{category}] 카테고리의 정보입니다.

## 오늘 수집된 핵심 사실
{current_facts[:4000]}

## 이전 브리핑 요약 (최근)
{prev_context[:2000]}

다음을 분석하세요:
1. **신규**: 이전에 없던 완전히 새로운 정보
2. **변화**: 이전과 달라진 내용 (버전 업, 상태 변경 등)
3. **트렌드**: 반복적으로 나타나는 패턴이나 방향성

간결하게 불릿 포인트로 작성. 한국어로."""

    result = claude_cli(prompt, model="sonnet", timeout=120)
    return result or "(트렌드 분석 실패)"


def cross_category_analysis(all_category_facts: dict[str, str]) -> str:
    """전체 카테고리의 사실을 모아 교차 분석."""
    if len(all_category_facts) < 2:
        return ""

    # 각 카테고리에서 상위 5개 사실만
    summary_parts: list[str] = []
    for cat, facts in all_category_facts.items():
        top_facts = "\n".join(facts.split("\n")[:5])
        summary_parts.append(f"## {cat}\n{top_facts}")

    combined = "\n\n".join(summary_parts)

    prompt = f"""아래는 UE5 애니메이션 각 카테고리별 핵심 사실입니다.

{combined[:5000]}

카테고리 간 **교차 분석**을 수행하세요:
1. **연관성**: 서로 관련 있는 카테고리 간 연결점 (예: Motion Matching + Mover Plugin)
2. **공통 트렌드**: 여러 카테고리에 공통적으로 나타나는 방향성
3. **TA 관점 시사점**: 기술 애니메이터에게 가장 중요한 연결고리

간결하게 불릿 포인트로 작성. 한국어로."""

    result = claude_cli(prompt, model="sonnet", timeout=120)
    return result or ""
