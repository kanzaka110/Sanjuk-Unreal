---
name: Groom IterationCount는 헤어 형태 유지의 핵심 — 후퇴시키지 마
description: XPBD에서 IterationCount ↑ → constraint compliance ↓ → effective stiffness ↑. 사용자 경험 검증된 사실.
type: feedback
originSessionId: 6d37eb50-96ec-4182-8e48-1395df67c432
---
# Groom IterationCount는 형태 유지 핵심

## 룰

PC_01 헤어 튜닝 시 **IterationCount는 절대 후퇴시키지 마**. 사용자가 의도적으로 높은 값(Grp 0=300)을 사용 중이며, 형태 유지의 핵심 메커니즘.

## Why

XPBD 메커니즘:
- IterationCount ↑ → constraint solver가 한 timestep 내에서 위배를 더 많이 수렴
- 결과: BendStiffness/StretchStiffness가 effective하게 더 단단하게 동작 (compliance ↓)
- → 헤어 root 영역 형태 유지 ↑, 처짐 ↓

사용자 직접 검증 (2026-04-29): "IterationCount 높여야 헤어 유지력이 좋아지던걸??"

이전에 "씬 전환 튐의 원인이 IterationCount=300"이라고 단정 처방한 게 잘못된 추론이었음. 진짜 튐 원인은 ProjectStretch=True / GravityPreloading=0 / underdamped Bend (별도 메모리).

## How to apply

- 헤어 jitter/튐 진단 시 **IterationCount는 용의자에서 제외**
- 형태 유지 보강이 필요하면 IterationCount ↑를 **유효한 처방으로 권장** 가능 (Grp 1/3/4의 8/6 → 16~24)
- CPU 비용 우려 시: SubSteps은 줄여도 IterationCount는 유지 (per-step 연산이 SubSteps × Iter)
- 형태 유지가 중요한 hero strand는 Iter 100~300까지 충분히 가능

## 반례

- 단, IterationCount + ProjectStretch=True 조합은 큰 dt(프레임 드랍) 시 폭발 위험 ↑. 이때는 **ProjectStretch를 False로 바꾸는 게 정답이지, IterationCount를 줄이는 게 아님**
