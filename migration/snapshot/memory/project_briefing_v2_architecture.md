---
name: briefing.py v2 아키텍처
description: briefing v2의 5 STEP 파이프라인, 품질 개선 13건, 모듈 구조, 모델 배분 정리
type: project
originSessionId: 783524ac-7688-486c-aaaf-e114422265c6
---
briefing.py v2 (2026-04-12, 품질개선 커밋 9f84bf2)는 7개 모듈, 5 STEP 파이프라인으로 구성.

**Why:** v1의 7개 문제 해결 + 토큰 최적화 후 품질 하락 13건 보완.

**How to apply:**

## 5 STEP 파이프라인
1. 다중소스 검색 (DDGS text+news + Claude CLI 보완, 카테고리별 특화 키워드)
2. 품질 검증 (관련성 40% 가중치) → 미달 시 보완 재검색 (최대 2라운드)
3. Map-Reduce 핵심사실 추출 (haiku, 5000자 청크) + **사실 수준 조기 중복 체크**
4. 교차 분석 (**원본 facts** 사용) + 이전 브리핑 트렌드 비교 (sonnet)
5. 메타데이터(haiku) + 본문(sonnet, 구조화 프롬프트) + **URL 환각 자동 제거**

## 모델 배분
- haiku: 사실 추출(map, 5000자 청크), 메타데이터
- sonnet: 웹검색, 트렌드/교차 분석, 본문 생성 (opus→sonnet 전환)
- DDGS text+news 1차 → Claude CLI 보완 (카테고리 키워드 활용)

## 품질 개선 (13건, 토큰 비용 0 또는 절감)
- 검색: DDGS news API, timelimit, CATEGORY_KEYWORDS, UE 관련성 필터, 보일러플레이트 제거
- 추출: 유사 중복 제거(70%), 소스 신뢰도 태그(★★★~★☆☆), 소스 우선순위 프롬프트
- 생성: 영상 섹션 조건부, URL 환각 제거, 구조화 프롬프트
- 효율: 조기 중복 차단(STEP 4~5 스킵), 교차분석 facts 전환

## 핵심 데이터 구조
- `SourcedResult`: url, title, snippet, source_type(claude_web/ddgs/ddgs_news), domain
- `QualityScore`: source_diversity(30%), count(30%), **relevance(40%)**, overall
- `CATEGORY_KEYWORDS`: 13개 카테고리별 특화 검색 키워드
- `_TRUST_TIERS`: 도메인별 소스 신뢰도 등급

## CLI 호환성
기존 인터페이스 100% 유지: --all, --category, --count, --force, --per-version
