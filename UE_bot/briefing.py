#!/usr/bin/env python3
"""
🎮 UE 애니메이션 데일리 브리핑 v2
GitHub Actions / cron 으로 매일 9시 KST에 자동 실행됩니다.

v2 개선사항:
  - 다중소스 검색 (Claude CLI + DuckDuckGo)
  - Map-Reduce 핵심사실 추출 (데이터 절삭 제거)
  - 검색 품질 검증 + 조건부 재검색
  - 교차 분석 + 트렌드 추적
  - 모듈 분리 (7개 파일)

사용법:
  python briefing.py                           # 오늘 3개 카테고리 (날짜 시드)
  python briefing.py --count 5                 # 5개 카테고리
  python briefing.py --all                     # 전체 카테고리
  python briefing.py --category "Control Rig"  # 특정 카테고리
"""

from __future__ import annotations

import argparse
import os
import random
import sys
import time
from datetime import date
from pathlib import Path

# ─── 의존성 로드 ──────────────────────────────────────────────────────────────

def _load_env() -> None:
    if os.getenv("CI"):
        return
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            print("📄 .env 파일 로드 완료")
    except ImportError:
        pass

_load_env()

from notion_client import Client

from briefing_config import CATEGORIES, UE_VERSIONS
from briefing_search import search_with_retry, results_to_text
from briefing_analyze import map_reduce_extract, analyze_trends, cross_category_analysis
from briefing_generate import generate_metadata, generate_body, make_fallback
from briefing_notion import (
    already_briefed_today, get_existing_summaries,
    is_content_duplicate, remove_new_badges, upload_to_notion,
)
from briefing_telegram import send_telegram

# ─── 설정 ─────────────────────────────────────────────────────────────────────

NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "4fd756cb968d4439b9e80bbc69184a57")
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


# ─── 콘텐츠 파이프라인 ────────────────────────────────────────────────────────

def fetch_content(
    category: str,
    *,
    target_version: str | None = None,
    previous_summaries: list[dict] | None = None,
    force: bool = False,
) -> dict | None:
    """5 STEP 파이프라인으로 콘텐츠 수집 → 분석 → 생성."""
    ver_label = f" (UE {target_version})" if target_version else ""
    print(f"  🔍 검색 중 ({category}{ver_label})...")

    try:
        # ── STEP 1-2: 다중소스 검색 + 품질 검증 + 재검색 ──
        results = search_with_retry(category)
        if not results:
            print(f"  ℹ️ {category}: 검색 결과 없음")
            return {}

        raw_text = results_to_text(results)
        print(f"  📄 수집 완료 ({len(raw_text)}자, {len(results)}건)")

        # ── STEP 3: Map-Reduce 핵심사실 추출 ──
        print(f"  🧠 핵심사실 추출 중...")
        facts = map_reduce_extract(raw_text, category)
        if not facts.strip():
            print(f"  ℹ️ {category}: 핵심사실 추출 실패")
            return {}

        # ── STEP 3.5: 조기 중복 체크 (STEP 4~5 비용 절약) ──
        if not force and previous_summaries:
            fact_words = set(facts.lower().split())
            for existing in previous_summaries:
                if existing.get("category") != category:
                    continue
                existing_text = existing.get("text", "")
                if not existing_text:
                    continue
                existing_words = set(existing_text.lower().split())
                if len(fact_words) < 5 or len(existing_words) < 5:
                    continue
                overlap = len(fact_words & existing_words)
                similarity = overlap / min(len(fact_words), len(existing_words))
                if similarity >= 0.6:
                    print(f"  ⏭  사실 수준 중복 감지 ({similarity:.0%}) — STEP 4~5 스킵")
                    return {}

        # ── STEP 4: 트렌드 분석 ──
        print(f"  📊 트렌드 분석 중...")
        trend_context = analyze_trends(
            facts, category, previous_summaries or [],
        )

        # ── STEP 5a: 메타데이터 추출 ──
        print(f"  📋 메타데이터 추출 중...")
        meta = generate_metadata(category, facts)

        if not force and not meta.get("새_정보_여부", True):
            print(f"  ℹ️ {category}: 최근 3일 내 신규 정보 없음 — 스킵")
            return {}

        print(f"  📋 메타데이터: {meta.get('제목', category)[:50]}...")

        # ── STEP 5b: 본문 생성 ──
        print(f"  📝 본문 생성 중...")
        body_markdown = generate_body(
            category, facts, trend_context, target_version,
        )
        print(f"  📝 본문 생성 ({len(body_markdown)}자)")

        return {
            "제목": meta.get("제목", f"{category} 브리핑 — {date.today().strftime('%Y.%m.%d')}"),
            "요약": meta.get("요약", "")[:2000],
            "소스_링크": meta.get("소스_링크", "https://dev.epicgames.com/documentation/ko-kr/unreal-engine"),
            "난이도": meta.get("난이도", "중급"),
            "UE_버전": meta.get("UE_버전", "5.7"),
            "태그": meta.get("태그", []),
            "카테고리": category,
            "본문_마크다운": body_markdown,
            "_facts": facts,  # 교차 분석용 원본 사실
        }

    except Exception as e:
        print(f"  ❌ 수집 오류 ({category}): {e}")
        return None


# ─── 메인 로직 ────────────────────────────────────────────────────────────────

def run_briefing(
    categories: list[str],
    *,
    force: bool = False,
    per_version: bool = False,
) -> None:
    """지정된 카테고리 목록에 대해 브리핑을 실행."""
    if not NOTION_API_KEY:
        print("❌ NOTION_API_KEY 환경변수가 없습니다.")
        sys.exit(1)

    notion_client = Client(auth=NOTION_API_KEY)

    # 버전별 분리 모드
    if per_version:
        tasks = [(cat, ver) for cat in categories for ver in UE_VERSIONS]
    else:
        tasks = [(cat, None) for cat in categories]

    print(f"\n{'='*60}")
    print(f"🎮 UE 애니메이션 데일리 브리핑 v2")
    print(f"📅 {date.today().strftime('%Y년 %m월 %d일')}")
    print(f"📂 대상: {len(tasks)}건 ({'버전별 분리' if per_version else '통합'})")
    if force:
        print(f"⚡ FORCE 모드 — 중복 체크 무시")
    print(f"{'='*60}\n")

    # 🆕 표기 정리
    print("🔄 이전 브리핑의 🆕 표기 정리 중...")
    removed = remove_new_badges(notion_client, NOTION_DATABASE_ID, api_key=NOTION_API_KEY)
    print(f"  → {removed}개 페이지에서 🆕 제거 완료\n")

    # 기존 브리핑 로드 (트렌드 비교 + 중복 체크용)
    print("📚 기존 브리핑 로드 중...")
    existing_summaries = get_existing_summaries(NOTION_DATABASE_ID, api_key=NOTION_API_KEY)
    print(f"  → {len(existing_summaries)}개 기존 요약 로드 완료\n")

    success, skipped, failed = 0, 0, 0
    telegram_results: list[dict] = []
    all_category_facts: dict[str, str] = {}

    # ── Phase A: 전체 카테고리 검색 + 사실 추출 ──
    category_data: dict[str, dict | None] = {}
    for idx, (category, version) in enumerate(tasks):
        label = f"{category} (UE {version})" if version else category
        print(f"\n[{idx+1}/{len(tasks)}] {label}")

        if not force and already_briefed_today(NOTION_DATABASE_ID, category, api_key=NOTION_API_KEY):
            skipped += 1
            continue

        if idx > 0:
            wait = 30
            print(f"  ⏳ Rate limit 방지 — {wait}초 대기...")
            time.sleep(wait)

        data = None
        for attempt in range(2):
            data = fetch_content(
                category,
                target_version=version,
                previous_summaries=existing_summaries,
                force=force,
            )
            if data is not None:
                break
            if attempt < 1:
                print(f"  🔄 재시도 2/2 — 30초 후...")
                time.sleep(30)

        category_data[(category, version)] = data

    # ── Phase B: 교차 분석 ──
    # all_category_facts에서 2개 이상 카테고리가 있으면 교차 분석
    fact_map: dict[str, str] = {}
    for (cat, _), data in category_data.items():
        if data and isinstance(data, dict) and data.get("본문_마크다운"):
            # 교차 분석에는 원본 사실 사용 (요약보다 정보량이 많음)
            fact_map[cat] = data.get("_facts", "") or data.get("요약", "")

    if len(fact_map) >= 2:
        print(f"\n🔗 교차 분석 중 ({len(fact_map)}개 카테고리)...")
        cross_analysis = cross_category_analysis(fact_map)
        if cross_analysis:
            print(f"  ✅ 교차 분석 완료 ({len(cross_analysis)}자)")
    else:
        cross_analysis = ""

    # ── Phase C: Notion 업로드 ──
    for (category, version), data in category_data.items():
        if data is None:
            failed += 1
            continue
        if not data:
            skipped += 1
            continue

        # 버전별 모드 제목 처리
        if version:
            data["UE_버전"] = version
            if f"UE {version}" not in data.get("제목", ""):
                data["제목"] = f"[UE {version}] {data.get('제목', category)}"

        data["제목"] = f"🆕 {data.get('제목', category)}"

        # 내용 중복 체크
        if not force and is_content_duplicate(data.get("요약", ""), existing_summaries):
            print(f"  ⏭  기존 브리핑과 내용 중복 — 건너뜀")
            skipped += 1
            continue

        if upload_to_notion(notion_client, NOTION_DATABASE_ID, data):
            success += 1
            telegram_results.append({
                "category": category,
                "title": data.get("제목", "").replace("🆕 ", ""),
                "difficulty": data.get("난이도", ""),
                "version": data.get("UE_버전", ""),
                "summary": data.get("요약", ""),
                "url": data.get("소스_링크", ""),
            })
        else:
            failed += 1

    # 최종 리포트
    print(f"\n{'='*60}")
    print(f"📊 결과: ✅ {success}개 생성 | ⏭ {skipped}개 스킵 | ❌ {failed}개 실패")
    if cross_analysis:
        print(f"🔗 교차 분석: 완료")
    print(f"📌 Notion: https://www.notion.so/{NOTION_DATABASE_ID.replace('-', '')}")
    print(f"{'='*60}\n")

    send_telegram(
        telegram_results,
        bot_token=TELEGRAM_BOT_TOKEN,
        chat_id=TELEGRAM_CHAT_ID,
        notion_db_id=NOTION_DATABASE_ID,
    )

    if failed > 0 and success == 0 and skipped == 0:
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="UE 애니메이션 데일리 브리핑 v2")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="모든 카테고리")
    group.add_argument("--category", type=str, help="특정 카테고리")
    group.add_argument("--count", type=int, default=3, help="오늘 브리핑 수 (기본 3)")
    parser.add_argument("--force", action="store_true", help="중복 체크 무시 (재생성)")
    parser.add_argument("--per-version", action="store_true", help="UE 버전별 개별 페이지 생성")
    args = parser.parse_args()

    if args.all:
        targets = CATEGORIES
    elif args.category:
        if args.category not in CATEGORIES:
            print(f"❌ 알 수 없는 카테고리: {args.category}")
            print(f"   사용 가능: {', '.join(CATEGORIES)}")
            sys.exit(1)
        targets = [args.category]
    else:
        random.seed(date.today().toordinal())
        targets = random.sample(CATEGORIES, min(args.count, len(CATEGORIES)))

    run_briefing(targets, force=args.force, per_version=args.per_version)


if __name__ == "__main__":
    main()
