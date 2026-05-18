---
name: KawaiiPhysics 플러그인 로컬 캐시 + 개요
description: pafuhana1213/KawaiiPhysics (UE용 경량 pseudo-physics 본 시뮬). 머리카락/치마/꼬리 세컨더리 모션. UE 5.3~5.6 공식, 5.7 미검증, MIT 라이선스.
type: reference
originSessionId: abee917a-80bb-4cf4-a80c-e01a5e7ce6da
---
## 기본 정보
- 리포: https://github.com/pafuhana1213/KawaiiPhysics (v1.20.0, 2026-03-30)
- 라이선스: MIT (상업 가능)
- 지원: UE 5.3~5.6 공식. **UE 5.7은 `.uplugin` 미명시 → 소스 재빌드 필요 가능성**
- PhysX 의존 없음. AnimGraph 노드 1개로 셋업. Sphere/Capsule/Plane 충돌, Wind/Gravity 지원

## 로컬 캐시
```
C:\Users\SHIFTUP\.claude\projects\C--Dev-Sanjuk-Unreal\cache\kawaii_physics\
```
핵심 파일: `AnimNode_KawaiiPhysics.h` (60KB, 전 파라미터 struct), `KawaiiPhysicsLibrary.h` (32KB, BP API), `README_ja.md` (상세), uplugin/DataAsset 헤더들.

## Chaos Cloth와 구분

| 용도 | 선택 |
|------|------|
| 머리카락/꼬리/귀/리본 (얇은 세컨더리) | **KawaiiPhysics** |
| 망토/드레스/전체 의상 | **Chaos Cloth** |
| 치마 — 얇은 느낌 | KawaiiPhysics |
| 치마 — 주름진 복잡한 드레스 | Chaos Cloth |

KawaiiPhysics는 자기 충돌 제한적·네트워크 복제 미고려. 무거운 천은 Chaos.

## UE 5.7 호환 안 될 시 대안
- Anim Dynamics Node (UE 내장)
- Control Rig Physics (UE 5.4+)
- VRM SpringBone 계열

## How to apply
- 머리카락/치마 흔들림 질문 시 위 표로 판단
- 파라미터 정확값은 `cache/kawaii_physics/AnimNode_KawaiiPhysics.h` Read
- UE 5.7 호환 이슈: https://github.com/pafuhana1213/KawaiiPhysics/issues
