# 7. 성능 최적화

## 7.1 왜 성능이 중요한가?

천 시뮬레이션은 **CPU를 많이 사용**합니다. 최적화 없이 캐릭터마다 천을 달면 프레임이 급격히 떨어집니다.

```
[최적화 없이]                    [최적화 후]

  캐릭터 10명 × 풀 시뮬           캐릭터 10명
  → 20 FPS 😱                   → 주인공만 풀 시뮬
                                 → NPC는 LOD로 경량화
                                 → 60 FPS 😊
```

### 성능 비용 공식

```
총 비용 ≈ 파티클 수 × Iteration × Substep
        + Self Collision (O(n²) — 가장 비싼!)
        + 콜리전 바디 수 × 파티클 수
```

> **Self Collision이 가장 비싼 연산입니다.** 꼭 필요한 경우에만 켜세요.

## 7.2 LOD — 가장 효과적인 최적화

LOD(Level of Detail)는 **카메라가 멀어질수록 품질을 줄이는** 전략입니다.

### LOD 3단계 구성

```
[LOD 0 — 근거리]              카메라에서 0~15m
  풀 시뮬레이션
  고해상도 메시
  Self Collision ON (선택적)
  Iteration 5~8
  → 최고 품질, 최대 비용

[LOD 1 — 중거리]              카메라에서 15~30m
  경량 시뮬레이션
  중해상도 메시 (Remesh 노드로 밀도 50% 감소)
  Self Collision OFF
  Iteration 2~3
  → 중간 품질, 중간 비용

[LOD 2 — 원거리]              카메라에서 30m+
  시뮬레이션 비활성화
  저해상도 스킨 메시만
  → 최저 비용 (거의 무료)
```

### LOD 전환 거리 가이드

| 게임 유형 | LOD 0→1 | LOD 1→2 |
|----------|---------|---------|
| 3인칭 액션 | 10~15m | 25~30m |
| 오픈 월드 RPG | 8~12m | 20~25m |
| 시네마틱 | 20m+ | 40m+ |

### 설정 방법 (Dataflow)

```
Panel Cloth (Dataflow) 에디터에서:

Collection 0 (LOD 0): 원본 메시 + 풀 파라미터
Collection 1 (LOD 1): Remesh 노드 추가 → 밀도 감소
Collection 2 (LOD 2): 시뮬레이션 미포함
```

## 7.3 파티클 수 줄이기

### Particle Distance 조절

Particle Distance를 늘리면 삼각형 수가 줄어들어 파티클이 감소합니다.

```
Particle Distance 1.0  → ~2,000 파티클  (고품질)
Particle Distance 2.0  → ~500 파티클    (균형)
Particle Distance 3.0  → ~200 파티클    (성능 우선)
```

### 파티클 수 예산

| 대상 | 파티클 수 | 이유 |
|------|----------|------|
| 주인공 의상 | 500~1,500 | 항상 가까이 보이므로 |
| 중요 NPC | 300~500 | 대화 시 가까이 봄 |
| 배경 NPC | 100~200 | 멀리서만 보임 |
| 군중 | 0 (시뮬 OFF) | 차이를 느끼지 못함 |

### Max Distance 0 영역 활용

```
Max Distance = 0인 버텍스는 시뮬레이션에서 제외됩니다.

[Before]  전체 메시의 70%가 자유       → 파티클 700개 시뮬
[After]   고정 영역을 50%로 확대       → 파티클 500개 시뮬 (30% 절약!)

→ 시각적 차이가 적은 부위(어깨 위, 허리 윗부분)를 고정하세요
```

## 7.4 Self Collision 최적화

Self Collision은 **끄는 것만으로** 큰 성능 향상을 얻습니다.

| 전략 | 효과 | 방법 |
|------|------|------|
| 완전 비활성화 | **최대 절약** | Self Collision OFF |
| 외부 레이어만 ON | 높음 | 내부 레이어는 보이지 않으므로 OFF |
| LOD 1 이상에서 OFF | 높음 | 멀리서는 차이 없음 |
| Buckling Stiffness 대체 | 중간 | Self Collision 없이 교차 줄이기 |

## 7.5 솔버 최적화

### Iteration Count

```
[비용 낮음]    Iteration 2~3   → 모바일, 배경 NPC
[균형]         Iteration 3~5   → 게임플레이 (60fps 목표)
[비용 높음]    Iteration 10+   → 시네마틱 전용
```

### Substep

```
[기본]         Substep 1       → 대부분의 상황에서 충분
[빠른 액션]    Substep 2~3     → 관통 문제 해결용
```

> **기억:** Iteration × Substep = 곱셈 비용. 둘 다 올리면 급증!

## 7.6 플랫폼별 예산 가이드

### PC (하이엔드)

```
주인공:    1,000~1,500 파티클, Self Collision ON, Iteration 5~8
동료 NPC:  500~800 파티클,    Self Collision OFF, Iteration 3~5
배경 NPC:  200~300 파티클,    Self Collision OFF, Iteration 2~3
```

### 콘솔 (PS5 / Xbox Series X)

```
주인공:    500~1,000 파티클, Self Collision 선택적, Iteration 3~5
동료 NPC:  300~500 파티클,   Self Collision OFF,   Iteration 2~3
배경 NPC:  시뮬 OFF
```

### 모바일

```
주인공:    100~300 파티클, Self Collision OFF, Iteration 1~2
기타:      시뮬 OFF
```

## 7.7 프로파일링 — 비용 측정하기

### stat Cloth 명령어

```
게임 실행 중:
1. ` (백틱) 키로 콘솔 열기
2. "stat Cloth" 입력 → Enter
3. 화면에 Cloth 시뮬레이션 비용이 표시됨
```

### 수치 읽는 법

| 지표 | 정상 | 주의 | 위험 |
|------|:----:|:----:|:----:|
| Cloth 시뮬 시간/프레임 | < 1ms | 1~3ms | > 3ms |
| 화면 내 총 파티클 | < 5,000 | 5,000~10,000 | > 10,000 |

```
[정상]  Cloth: 0.5ms → 60fps에 여유 있음 ✅
[주의]  Cloth: 2.5ms → 다른 요소와 합치면 위험할 수 있음 ⚠️
[위험]  Cloth: 5.0ms → 프레임 드롭 확실 ❌
        → 파티클 줄이기, Self Collision 끄기, LOD 설정 필요
```

### Unreal Insights (고급)

더 상세한 프로파일링이 필요하면:

```
1. Edit → Editor Preferences → "Unreal Insights" 검색
2. 또는 콘솔에서 "Trace.Start" 입력
3. Session Frontend에서 Cloth 관련 타이밍 분석
```

## 7.8 최적화 체크리스트 (요약)

```
□ LOD 설정했는가?
  └─ 원거리에서 시뮬 OFF가 가장 큰 절약

□ 파티클 수가 예산 내인가?
  └─ stat Cloth로 확인

□ Self Collision이 꼭 필요한가?
  └─ 아니면 Buckling Stiffness로 대체

□ Iteration/Substep이 적절한가?
  └─ 3~5로 시작, 관통 발생 시에만 올리기

□ Max Distance 0 영역을 충분히 넓혔는가?
  └─ 시뮬 안 해도 되는 부분은 고정

□ 배경 NPC의 천 시뮬은 꺼져 있는가?
  └─ 멀리서는 차이를 못 느낌
```

## 체크리스트

- [ ] LOD 개념과 3단계 구성 이해
- [ ] 파티클 수 예산 계획 수립
- [ ] Self Collision 필요성 판단
- [ ] stat Cloth로 성능 측정 방법 파악
- [ ] 플랫폼별 예산 가이드 참고

---
[← 이전: 멀티레이어 의상](06-Multilayer-Clothing.md) | [다음: 트러블슈팅 →](08-Troubleshooting.md)
