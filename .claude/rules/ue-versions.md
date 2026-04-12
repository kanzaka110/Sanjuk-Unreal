# UE 버전별 주요 변경사항 참조

## UE 5.5 → 5.6 주요 변경

- **AnimNext 프리뷰** — UAF 첫 도입, Workspace/Module/TraitStack 개념
- **Motion Matching** — Pose Search 정식 도입, 데이터베이스 기반 포즈 선택
- **Chooser Table** — State Machine 대안으로 조건 테이블 시스템
- **Enhanced Input** — 기존 Input 완전 대체 (레거시 Input 제거 예정)
- **Nanite 개선** — 스켈레탈 메시 지원 확대 (Masked 머티리얼)

## UE 5.6 → 5.7 주요 변경

- **AnimNext 정식화** — UAF 프로덕션 사용 가능 수준
- **Monolith 호환** — MCP 기반 AI 에디터 제어 (v0.12.0)
- **StateTree 개선** — AI 상태 관리 강화, Logic Driver 연동
- **Chaos Cloth 개선** — 성능 최적화, 풍력 시뮬레이션 정밀도
- **MetaHuman 5.7** — 신규 바디 타입, 페이셜 개선

## AnimNext (UAF) 마이그레이션 핵심 체크포인트

ABP에서 전환할 때 반드시 확인:

1. EventGraph 로직 → Module로 이전
2. State Machine → Chooser Table + Motion Matching으로 대체
3. AnimInstance 변수 → Shared Variables로 이전
4. Blend Node 트리 → TraitStack (Base + Additive)으로 재구성
5. Transition Rule → Chooser Row 조건으로 변환
6. AnimNotify → 그대로 호환 (변경 불필요)
7. Montage → 그대로 호환 (슬롯 기반 블렌딩 유지)

## Chaos Cloth 자주 쓰는 파라미터

| 파라미터 | 기본값 | 용도 | 권장 범위 |
|---------|--------|------|----------|
| Wind Velocity | (0,0,0) | 풍력 방향/세기 | 100~500 cm/s |
| Damping | 0.01 | 진동 감쇄 | 0.01~0.1 |
| Friction | 0.8 | 표면 마찰 | 0.5~1.0 |
| Gravity Scale | 1.0 | 중력 배율 | 0.5~2.0 |
| Stiffness | 1.0 | 천 단단함 | 0.1~10.0 |
| Mass | 1.0 | 질량 | 0.1~5.0 |
| Collision Thickness | 1.0 | 충돌 두께 | 0.5~3.0 cm |
| Self Collision | false | 자기 충돌 | 성능 비용 높음 |

## Physics Asset 콜리전 가이드

- **Capsule** — 팔, 다리 등 원통형 부위 (가장 효율적)
- **Sphere** — 관절, 머리 등 구형 부위
- **Box** — 몸통 등 직육면체 부위 (드물게 사용)
- 콜리전 볼륨은 메시보다 약간 작게 (관통 방지)
- 최대 20~30개 콜리전 바디 권장 (성능)
