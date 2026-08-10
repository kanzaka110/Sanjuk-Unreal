# UE5 도메인 지식

## 핵심 용어 & 개념

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| ABP | Animation Blueprint | 애니메이션 로직 그래프 (레거시, UAF로 전환 중) |
| UAF | Universal Animation Framework | AnimNext 기반 차세대 애니메이션 시스템 |
| TraitStack | — | Base Trait + N개 Additive Trait 구성 (Motion Matching + Aim Offset + Lean 등) |
| Chooser Table | — | 조건 테이블 기반 에셋 선택 (State Machine 대체) |
| GAS | Gameplay Ability System | 어빌리티, 어트리뷰트, 게임플레이 이펙트 |
| EQS | Environment Query System | AI 환경 쿼리 |
| Control Rig | — | 프로시저럴 리깅, 본 트랜스폼 제어 |

## ABP → UAF 용어 매핑

- AnimBlueprint → Workspace
- AnimInstance → AnimNextComponent
- EventGraph → Module
- AnimGraph → Animation Graph + TraitStack
- State Machine → Chooser Table + Motion Matching
- Node Tree → TraitStack
- Transition Rule → Chooser Row

## 애니메이션 에셋 계층

1. **AnimSequence** — 단일 클립 (본 트랙, 커브, 노티파이)
2. **AnimMontage** — 섹션 기반 분할 (Windup→Strike→Recovery), 슬롯 블렌딩
3. **BlendSpace** — 1D(Speed) / 2D(Direction×Speed) / Aim Offset(Yaw×Pitch)
4. **State Machine** — 상태 전환 (Idle→Walk→Jog→Sprint→Jump→Fall→Land)

## 작업 시 참고 원칙

- 에셋 경로는 항상 `/Game/...` 형식 사용, 에디터에서 "Copy Reference"로 확인
- Bone 이름은 UE 스켈레톤 기준 (pelvis, spine_01, spine_02, ...)
- 애니메이션 커브는 소문자_언더스코어 (speed, direction, lean_amount)
- Root Motion: 캐릭터 이동은 애니메이션이 아닌 Movement Component 권장 (네트워크 동기화)
