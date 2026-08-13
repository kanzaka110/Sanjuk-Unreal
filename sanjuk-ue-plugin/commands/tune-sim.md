---
name: tune-sim
description: Simulation 튜닝 에이전트(sim-tuner) 호출 — Inspector 처방 필요
---

# /tune-sim — Simulation 튜닝 에이전트 호출

Sim Inspector 가 제시한 처방을 **실제 Groom / Cloth / Physics Asset 에 적용**. Monolith HTTP API + before/after 비교.

## 호출 형식

사용자 발화 예:
- `/tune-sim 방금 진단 적용`
- `/tune-sim Grp 4 Gravity -1 → -0.5`
- `/tune-sim Cloth Damping 0.01 → 0.05`

## ⚠ 사전 조건 (강제)

1. **Inspector 처방이 반드시 선행** — 단독 호출 금지
2. **dry-run 명시** — 어떤 파라미터가 어떻게 바뀌는지 사전 출력
3. **백업 자동 생성** — 변경 전 그룹별 dump 보존
4. **그룹/슬롯 단위 단일 변경** — 한 번에 여러 그룹 동시 변경 금지 (side effect 추적 가능하게)

## 실행 지침

Agent tool 의 `subagent_type=sim-tuner` 로 호출. prompt 에 포함:

1. **Inspector 처방 spec** (필수): 그룹/슬롯/파라미터/값
2. **자산 경로**
3. **백업 dump 위치**
4. **PIE 검증 대상**: 변경 후 시각 동작 ([[feedback-visual-mesh-over-anim-rec]])

## Tuner 가 자동 수행

- before-dump (그룹별 active config)
- 파라미터 변경 (1 그룹씩, batch 가능)
- save_asset
- after-dump + diff
- PIE 검증 안내

## 사용 안 할 때

- 처방 없이 사용자가 직접 한 그룹만 짧게 변경 → `Bash` 로 set_pc01_hair_*.py 직접

## 호출 후 자동 후속

- save 실패 시 P4 안내
- after = before (변경 안 적용) → 권한 / asset reference 문제 분석
- 시각 검증 실패 (사용자 호소) → 메모리 [[feedback-visual-mesh-over-anim-rec]] 참조

## 관련 메모리

- [[reference-sanjuk-agents]]
- [[reference-groom-physics-params]]
- [[pc01-hair-gravity-bug]]
