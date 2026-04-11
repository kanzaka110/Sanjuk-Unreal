# 1. Chaos Cloth 개요

## 1.1 Chaos Cloth란?

Chaos Cloth는 언리얼 엔진의 **파티클 기반 천 시뮬레이션 시스템**입니다.

쉽게 말하면, 게임 속 캐릭터의 **망토, 치마, 드레스, 깃발** 같은 천이 바람에 펄럭이고, 캐릭터가 달릴 때 따라 움직이고, 몸을 뚫지 않도록 만들어주는 기능입니다.

### 천 시뮬레이션이 없을 때 vs 있을 때

```
[시뮬레이션 없음]              [Chaos Cloth 적용]

  캐릭터가 달려도               캐릭터가 달리면
  망토가 딱딱하게               망토가 뒤로 펄럭이고
  몸에 붙어 있음                바람에 자연스럽게 반응
       😐                          😮
```

### 핵심 특징

- **파티클 시뮬레이션** — 천의 각 꼭짓점(버텍스)을 물리 입자로 취급하여 중력, 바람, 충돌에 반응
- **듀얼 메시 파이프라인** — 물리 연산용 저해상도 메시 + 화면 표시용 고해상도 메시 자동 연결
- **Physics Asset 기반 충돌** — 캡슐/구체 형태의 충돌 볼륨으로 천이 캐릭터 몸을 뚫지 않게 방지
- **노드 기반 에디터** — Panel Cloth, Dataflow Editor로 시각적 워크플로우 (UE 5.3+)

### 어디에 쓰이나?

| 용도 | 예시 |
|------|------|
| 캐릭터 의상 | 망토, 치마, 코트 자락, 리본, 술 |
| 환경 오브젝트 | 깃발, 커튼, 텐트, 현수막 |
| 시네마틱 | 드레스 펼쳐짐, 후드 벗기 연출 |
| 메타휴먼 | 커스텀 의류 시뮬레이션 |

## 1.2 발전 역사

| UE 버전 | 주요 변화 | 초보자 참고 |
|---------|----------|-----------|
| 4.x | 구 Cloth 시스템 (APEX Cloth → NvCloth) | 더 이상 사용하지 않음 |
| 5.0~5.2 | Chaos Cloth 기본 도입, APEX/NvCloth 대체 | Clothing Tool 사용 |
| 5.3 | **Panel Cloth** 노드 에디터 도입 | 패턴 기반 천 생성 가능 |
| 5.4 | Panel Cloth 예제 파일, Dataflow 충돌 업데이트 | 예제 파일로 학습 권장 |
| 5.5 | 안정성 개선, 페인팅 도구 개선 | **초보자 추천 시작 버전** |
| 5.6 | **Unified Dataflow Editor** (Experimental), **Outfit Asset** | Cloth-to-Cloth 컨스트레인트, 모프 타겟 지원 |
| 5.7 | 타임라인/시뮬 컨트롤 개선, 페인팅 도구 통합 | Skeletal Mesh 에디터 페인팅 도구 포팅 |

> **중요:** 각 UE 버전에서 Chaos Cloth가 크게 바뀝니다. 5.4 가이드를 5.7에서 따르면 메뉴가 다를 수 있습니다. 반드시 **자신의 UE 버전에 맞는 정보**를 참고하세요.

## 1.3 두 가지 방식: Clothing Tool vs Panel Cloth

Chaos Cloth를 셋업하는 방법은 **두 가지**가 있습니다. 초보자는 Clothing Tool부터 시작하세요.

| 구분 | Clothing Tool (기본) | Panel Cloth (고급) |
|------|---------------------|-------------------|
| **UE 버전** | 5.0+ 모두 사용 가능 | 5.3+ |
| **방식** | SkeletalMesh 에디터에서 직접 페인팅 | 노드 기반 Dataflow 그래프 |
| **난이도** | **초보자 추천** | 중급 이상 |
| **사용 사례** | 간단한 망토, 깃발, 커튼 | 복잡한 의류, 멀티레이어, AAA |
| **유연성** | 제한적 | 높음 (노드 조합 자유) |

> 이 가이드에서는 **Clothing Tool (기본 방식)을 먼저** 배우고, Panel Cloth는 심화 과정에서 다룹니다.

## 1.4 핵심 개념 — 처음 알아야 할 5가지

### 개념 1: Sim Mesh와 Render Mesh

```
[Sim Mesh]                    [Render Mesh]
저해상도 (삼각형 적음)          고해상도 (삼각형 많음)
    ┌───┐                      ┌─────────┐
    │ △ │  ← 물리 연산용       │ △△△△△△ │ ← 화면 표시용
    │△ △│     (가볍고 빠름)    │△△△△△△△│    (예쁘고 세밀)
    └───┘                      └─────────┘
        │                           ↑
        └── 물리 결과를 자동 전달 ──┘
```

- **Sim Mesh**: 물리 연산을 담당하는 단순한 메시. 꼭짓점(=파티클) 수가 적어 빠릅니다.
- **Render Mesh**: 실제로 화면에 보이는 세밀한 메시. Sim Mesh의 결과를 받아 변형됩니다.
- 기본 Clothing Tool에서는 하나의 메시가 두 역할을 겸하며, Panel Cloth에서는 분리할 수 있습니다.

### 개념 2: Max Distance (최대 거리)

각 꼭짓점이 원래 위치에서 **얼마나 멀리 움직일 수 있는지** 정합니다.

```
Max Distance = 0   →  고정됨 (움직이지 않음)  →  어깨, 허리밴드
Max Distance = 10  →  10cm까지 움직임         →  팔꿈치 근처
Max Distance = 50  →  50cm까지 움직임         →  치마 밑단, 망토 끝
```

> "페인팅"으로 설정합니다 — 검정(고정) ↔ 흰색(자유)으로 칠합니다.

### 개념 3: Backstop (뒤쪽 벽)

천이 캐릭터 **안쪽(몸 쪽)으로 뚫고 들어가는 것을 막는** 보이지 않는 벽입니다.

```
          ← 바깥 (천이 움직이는 방향)
   ┌─────────────┐
   │  시뮬 가능   │ ← Max Distance 범위
━━━●━━━━━━━━━━━━━━  ← 스킨 표면 (캐릭터 몸)
   │ 🚫 진입 금지 │ ← Backstop이 막는 영역
   └─────────────┘
          → 안쪽 (몸 안)
```

### 개념 4: Physics Asset (충돌 볼륨)

Physics Asset은 캐릭터의 몸 주위에 **보이지 않는 캡슐/구체**를 배치해서, 천이 캐릭터를 뚫지 않도록 합니다.

```
캐릭터 실루엣        Physics Asset (와이어프레임)

    ○  머리             ○  Sphere
   ┃┃  목              ║║  Capsule
  ┏━━┓ 몸통          ┌╌╌╌┐ Capsule
  ┃  ┃               ╎   ╎
  ┗━━┛               └╌╌╌┘
  / \  다리           / \  Capsule × 2
```

### 개념 5: 천 시뮬레이션의 흐름

```
매 프레임:
1. 캐릭터가 움직임 (애니메이션)
2. Physics Asset 캡슐이 따라 움직임 (Kinematic)
3. Chaos Cloth가 천 파티클의 새 위치를 계산
   - 중력, 바람, Drag/Lift 적용
   - Max Distance 범위 내로 제한
   - Backstop으로 안쪽 관통 방지
   - Physics Asset 캡슐과 충돌 체크
4. Sim Mesh 결과를 Render Mesh에 전달
5. 화면에 표시
```

## 1.5 플러그인 활성화 (필수!)

Chaos Cloth를 사용하려면 플러그인을 켜야 합니다.

### 단계별 가이드

```
1. UE 에디터 상단 메뉴 → Edit → Plugins
2. 검색창에 "Chaos Cloth" 입력
3. 두 개의 플러그인을 모두 체크:
   ☑ Chaos Cloth
   ☑ Chaos Cloth Asset
4. 에디터 재시작 (Restart Now 버튼)
```

> **확인:** 재시작 후 Content Browser에서 우클릭 → Physics 하위 메뉴에 "Chaos Cloth Asset"이 보이면 성공입니다.

## 1.6 이 가이드의 학습 경로

```
[초보자 코스]                    [중급 코스]                    [고급 코스]
01. 개요 (지금 여기!)           04. 충돌 설정                  07. 성능 최적화
02. Physics Asset 기초          05. 파라미터 튜닝              08. 트러블슈팅
03. Cloth 기본 셋업             06. 멀티레이어 의상            09. AAA 파이프라인
    └─ 실습: 깃발 만들기            └─ 실습: 캐릭터 망토         10. 참고 자료
    └─ 실습: 캐릭터 치마 셋업
```

### 출처

이 가이드는 다음 자료를 기반으로 작성되었습니다:

| 출처 | 유형 | 초점 |
|------|------|------|
| [Chaos Cloth for AAA Games](https://youtu.be/1ty5-RlBlVQ) (Unreal Fest Orlando 2025) | 공식 발표 | AAA 파이프라인 |
| [Tips and Tricks for Cloth Dynamics](https://youtu.be/wq0lY7vhF5w) (Unreal Fest Bali 2025) | 공식 발표 | 실전 팁 |
| [Chaos Cloth Tool Overview](https://dev.epicgames.com/community/learning/tutorials/OPM3/unreal-engine-chaos-cloth-tool-overview) | 공식 튜토리얼 | 기본 개요 |
| [Quick Start Guide for Cloth Simulation](https://dev.epicgames.com/community/learning/tutorials/KPxx/quick-start-guide-for-cloth-simulation-getting-started-in-unreal-engine-5) | 커뮤니티 | 초보자 퀵스타트 |
| [The Ultimate Guide to Simple Cloth (5.5)](https://dev.epicgames.com/community/learning/tutorials/RZ75/the-ultimate-guide-to-simple-cloth-in-unreal-engine-5-5-beginners-tutorial) | 커뮤니티 | 초보자 종합 |
| [Chaos Cloth Updates 5.7](https://dev.epicgames.com/community/learning/tutorials/1o0R/unreal-engine-chaos-cloth-updates-5-7) | 공식 튜토리얼 | 최신 업데이트 |

## 체크리스트

- [ ] Chaos Cloth가 무엇인지 이해
- [ ] Sim Mesh / Render Mesh 개념 이해
- [ ] Max Distance, Backstop, Physics Asset의 역할 이해
- [ ] Clothing Tool vs Panel Cloth 차이 이해
- [ ] 플러그인 활성화 완료 (Chaos Cloth + Chaos Cloth Asset)

---
[다음: Physics Asset 기초 →](02-Physics-Asset-Basics.md)
