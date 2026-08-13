---
name: inspect-abp
description: AnimBP 진단 에이전트(animbp-inspector) 호출
---

# /inspect-abp — AnimBP 진단 에이전트 호출

ABP / AnimGraph / State Machine / CDO 변수 / FootPlacement / LegIK / Control Rig 의 **현재 값 진단**.

## 호출 형식

사용자 발화 예:
- `/inspect-abp PC_01_ABP 의 IsTransition 게이트 현재 상태`
- `/inspect-abp FootPlacement PelvisSettings 3 프로필 값 비교`
- `/inspect-abp Sprint→Battle transition rule chain`

## 실행 지침

Agent tool 의 `subagent_type=animbp-inspector` 로 호출. 메인 에이전트가 아래 컨텍스트를 prompt 에 **반드시 포함**:

1. **자산 경로**: `/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP` (사용자가 다른 ABP 명시하면 그것)
2. **현재 작업 컨텍스트**: 메모리 [[pc01-session-end-2026-05-15]] 의 현재 최종 상태 한 줄
3. **관련 변수/노드**: 사용자 질문에 등장한 키워드
4. **선행 메모리**: 관련 reference_*.md / project_pc01_* 메모리 path
5. **카탈로그 / 최근 PoC 결과**: scripts/analyze_pc01_state_machines.py 산출물 (dumps/sm/) 활용 권장

## 에이전트가 반환할 형식

진단 보고 + 처방 spec (수정은 안 함). Tuner 호출용 spec 이 포함되면 사용자 확인 후 `/tune-abp` 로 이어감.

## 호출 후 자동 후속

- 진단 결과가 "값 X 로 변경 권장" 이면 사용자에게 `/tune-abp` 안내
- 처방 없이 단순 분석이면 거기서 종료

## 사용 안 할 때

- 단순 "X 변수 dump 만 받고 싶다" → `Bash` 또는 `Monolith` 직접 호출 (에이전트 호출은 분석/처방 필요할 때)
- AnimBP 외 영역 (Groom / Cloth / Physics Asset) → `/inspect-sim` 사용

## 관련 메모리

- [[reference-sanjuk-agents]] — 에이전트 4종 매트릭스
- [[reference-animation-query-sm-dump]] — SM dump 단일 진입점
- [[reference-monolith-animgraph-editing-limits]] — 알려진 한계
