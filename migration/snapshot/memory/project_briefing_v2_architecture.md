---
name: briefing.py v2 아키텍처
description: briefing v2의 5 STEP 파이프라인, 모듈 구조, 모델 배분 정리
type: project
---

briefing.py v2 (2026-04-12)는 7개 모듈, 5 STEP 파이프라인으로 구성.

**Why:** v1의 7개 문제(데이터 절삭, 검색 부족, 재검색 없음, 교차분석 없음, 트렌드 없음, DDGS 미활용, 소스 검증 없음) 전면 해결.

**How to apply:**

## 5 STEP 파이프라인
1. 다중소스 검색 (Claude CLI sonnet + DDGS, 8-15개 쿼리)
2. 품질 검증 → 미달 시 보완 재검색 (최대 2라운드)
3. Map-Reduce 핵심사실 추출 (haiku, 청크별 → 병합, 절삭 없음)
4. 교차 분석 (항상 ON) + 이전 브리핑 트렌드 비교 (sonnet)
5. 메타데이터(haiku) + 본문(opus) 생성

## 모델 배분
- haiku: 사실 추출(map), 메타데이터
- sonnet: 웹검색, 트렌드/교차 분석
- opus: 본문 생성

## 핵심 데이터 구조
- `SourcedResult`: url, title, snippet, source_type(claude_web/ddgs), domain
- `QualityScore`: source_diversity, freshness, count, overall

## CLI 호환성
기존 인터페이스 100% 유지: --all, --category, --count, --force, --per-version
