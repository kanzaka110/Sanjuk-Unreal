# FocalRig 플러그인 튜토리얼

> **FocalRig** — UE5용 프로시저럴 Look & Aim 플러그인 완전 가이드

## 개요

FocalRig은 Unreal Engine의 Control Rig 기반 플러그인으로, 기존 Aim Offset을 대체하는 **프로시저럴(절차적) 에이밍 시스템**입니다. 단일 포즈에서 풀바디 Look-At을 구현하며, 무기 반동, 눈 추적, 다리 보정까지 지원합니다.

## 대상 독자

- UE5 초보자 ~ 중급자
- 3인칭/1인칭 슈터 게임 개발자
- 애니메이션 시스템에 관심 있는 아티스트/프로그래머
- Control Rig을 활용하고 싶은 개발자

## 환경 요구 사항

| 항목 | 요구 사항 |
|------|----------|
| Unreal Engine | 5.3 이상 (5.5+ 권장) |
| FocalRig | Fab에서 구매/다운로드 |
| Control Rig 플러그인 | 활성화 필요 (UE 기본 제공) |
| 프로젝트 타입 | Blueprint 또는 C++ |

## 목차

| # | 제목 | 내용 |
|---|------|------|
| 01 | [FocalRig이란?](01-What-Is-FocalRig.md) | 개념, Aim Offset과의 차이, 왜 FocalRig인가 |
| 02 | [설치 및 프로젝트 설정](02-Installation.md) | Fab에서 다운로드, 플러그인 활성화, 프로젝트 설정 |
| 03 | [핵심 개념 이해하기](03-Core-Concepts.md) | Aim Chain, Eye Aim, Leg Adjustment, Quick Setup |
| 04 | [Quick Setup — 5분 만에 시작하기](04-Quick-Setup.md) | 자동 설정으로 빠르게 시작하기 |
| 05 | [Aim Chain 완전 정복](05-Aim-Chain.md) | 풀바디 에이밍, 스파인 회전, 타겟 추적 |
| 06 | [Eye Aim 시스템](06-Eye-Aim.md) | 눈 추적, Saccade, 스프링 댐핑 |
| 07 | [Recoil(반동) 시스템](07-Recoil-System.md) | 2D 패턴 에디터, 무기별 프리셋, 데이터 에셋 |
| 08 | [Leg Adjustment 시스템](08-Leg-Adjustment.md) | 발 고정, 골반 회전 보정 |
| 09 | [블루프린트 & Sequencer 연동](09-Blueprint-Sequencer.md) | BP에서 타겟 설정, Sequencer 키프레임 |
| 10 | [실전 예제 모음](10-Practical-Examples.md) | TPS 슈터, FPS, NPC 대화, 시네마틱 |

## 빠른 참조

```
FocalRig 핵심 노드 4가지:
├── Aim Chain      → 풀바디 에이밍 (스파인 → 타겟 방향 회전)
├── Eye Aim        → 눈 추적 (스프링 댐핑 + Saccade)
├── Recoil         → 무기/카메라 반동 (2D 패턴)
└── Leg Adjustment → 발 고정 (골반 회전 시 미끄러짐 방지)
```

## 공식 리소스

- [FocalRig 공식 사이트](https://focalrig.com/)
- [Fab 마켓플레이스](https://www.fab.com/) (FocalRig 검색)
- [UE5 Control Rig 공식 문서](https://dev.epicgames.com/documentation/en-us/unreal-engine/control-rig-in-unreal-engine)

---

> 💡 이 튜토리얼은 2026년 4월 기준 FocalRig 최신 버전을 기반으로 작성되었습니다.
