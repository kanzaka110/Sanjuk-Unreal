# Chaos Cloth & Physics Asset 가이드 - UE5 천 시뮬레이션 완전 정복

> 캐릭터의 망토, 치마, 드레스를 바람에 펄럭이게 만들고 싶다면?
> 이 가이드를 처음부터 따라하면 Chaos Cloth를 완전히 이해할 수 있습니다.
> 초보자도 깃발 하나 만드는 것부터 시작하여, AAA 프로덕션 파이프라인까지 단계적으로 배웁니다.

## 학습 경로

### 초보자 코스 (1~3장, 2~3시간)

| # | 챕터 | 내용 | 실습 |
|---|------|------|------|
| 1 | [Chaos Cloth 개요](01-Overview.md) | 시스템 소개, 핵심 개념 5가지, 플러그인 활성화 | — |
| 2 | [Physics Asset 기초](02-Physics-Asset-Basics.md) | 콜리전 바디 유형, 에디터 사용법, 크기 조절 | 마네킹 Physics Asset 만들기 |
| 3 | [Chaos Cloth 기본 셋업](03-Cloth-Setup.md) | Clothing Data 생성, Max Distance 페인팅, 첫 시뮬레이션 | **깃발 만들기, 캐릭터 치마** |

### 중급 코스 (4~6장, 3~4시간)

| # | 챕터 | 내용 | 실습 |
|---|------|------|------|
| 4 | [충돌 설정](04-Collision-Config.md) | Physics Asset 연결, 격리된 콜리전, Self Collision | 캐릭터 망토 충돌 설정 |
| 5 | [파라미터 튜닝](05-Parameter-Tuning.md) | 소재별 프리셋, 바람 효과, 솔버 설정 | 실크/가죽/망토 소재감 표현 |
| 6 | [멀티레이어 의상](06-Multilayer-Clothing.md) | 다층 의류, Outfit Asset (5.6+) | 셔츠+재킷 멀티레이어 |

### 고급 코스 (7~10장, 2~3시간)

| # | 챕터 | 내용 |
|---|------|------|
| 7 | [성능 최적화](07-Performance-Optimization.md) | LOD 전략, 파티클 예산, 프로파일링 |
| 8 | [트러블슈팅](08-Troubleshooting.md) | 흔한 5가지 문제, 디버깅 도구, FAQ |
| 9 | [AAA 프로덕션 파이프라인](09-AAA-Production-Pipeline.md) | DCC 연동, Panel Cloth, Baked Animation |
| 10 | [참고 자료](10-References.md) | 공식 문서, 영상, 학습 경로 총 30+ 링크 |

## 환경 요구사항

| 항목 | 요구사항 |
|------|---------|
| Unreal Engine | **5.5 이상** 권장 (Panel Cloth: 5.3+, Outfit Asset: 5.6+) |
| 필수 플러그인 | Chaos Cloth + Chaos Cloth Asset |
| 권장 DCC | Marvelous Designer, Maya, Blender (없어도 시작 가능) |
| 사전 지식 | UE5 에디터 기본 조작, SkeletalMesh 개념 |

## 출처

이 가이드는 다음 자료를 기반으로 작성되었습니다:

| 유형 | 출처 |
|------|------|
| 공식 발표 | [Chaos Cloth for AAA Games](https://youtu.be/1ty5-RlBlVQ) (Unreal Fest Orlando 2025) |
| 공식 발표 | [Tips and Tricks for Cloth Dynamics](https://youtu.be/wq0lY7vhF5w) (Unreal Fest Bali 2025) |
| 공식 튜토리얼 | Chaos Cloth Tool Overview, Properties Reference, Updates 5.6/5.7 |
| 커뮤니티 | Ultimate Guide to Simple Cloth, Quick Start Guide, Echo Cape Tutorial 외 다수 |
| 공식 문서 | Clothing Tool (5.7 Docs), Panel Cloth Editor Overview |

> 10장 참고 자료에서 **30개 이상의 링크**를 난이도별로 정리했습니다.
