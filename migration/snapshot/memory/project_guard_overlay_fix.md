---
name: Guard Overlay 다리 덜덜거림 수정 완료
description: PC_01 Guard Overlay + IK 충돌 해결. IK를 Overlay 앞으로 이동 + 다리/골반 레이어링 커브 0으로 설정.
type: project
originSessionId: e6d479b5-60ae-4f17-9866-6f6bdbc6b8cd
---
## 문제
Guard 오버레이 적용 시 다리 사이클이 덜덜거리며 꼬이는 현상.

## 원인
1. IK(FootPlacement)가 Overlay 뒤에서 실행 → Guard 오버레이가 pelvis를 미세하게 변경 → IK가 매 프레임 발 재배치 → 로코모션과 충돌
2. Guard 포즈의 `layering_legs=1`, `layering_pelvis=1` → 오버레이가 하체까지 영향

## 해결 (2026-04-16)
1. **PC_01_ABP AnimGraph 순서 변경**: `BlendStack → IK → Overlay → 출력` (IK를 Overlay 앞으로)
2. **Guard 포즈 커브 수정**: `layering_legs=0`, `layering_pelvis=0` (Idle/Move 모두)

## 시도한 조합 기록
| IK 위치 | legs/pelvis 커브 | 결과 |
|---------|:---:|------|
| Overlay 뒤 | 1 | 다리 덜덜거림 ❌ |
| Overlay 앞 | 1 | 비탈 IK 약함 ❌ |
| Overlay 앞 | 0 | **정상 ✅** |

**Why:** IK는 순수 로코모션 포즈 기반으로 계산, Overlay는 IK 결과 위에 상체만 블렌딩.

**How to apply:** 다른 Overlay 포즈 추가 시에도 layering_legs=0, layering_pelvis=0 설정 필요. IK와 Overlay 순서 유지.
