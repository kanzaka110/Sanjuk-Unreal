# 8. 트러블슈팅

## 8.1 "일단 이것부터 확인!" — 가장 흔한 5가지 문제

### 문제 1: 천이 전혀 안 움직인다

```
원인 (순서대로 확인):

1. ☐ 플러그인이 꺼져 있음
   → Edit → Plugins → "Chaos Cloth" 검색 → 둘 다 체크 → 재시작

2. ☐ Apply Clothing Data를 안 했음
   → SkeletalMesh 에디터 → 섹션 우클릭 → Apply Clothing Data

3. ☐ Max Distance 체크가 안 되어 있음
   → Masks 패널 → ☑ Max Distance 체크

4. ☐ Max Distance가 모두 0 (전부 검정)
   → Cloth Paint 모드 → 흰색으로 페인팅

5. ☐ Cloth Simulation이 비활성 상태
   → 뷰포트 → Enable Cloth Simulation 토글
```

### 문제 2: 천이 바닥으로 떨어진다

```
원인:
  고정 영역(Max Distance = 0)이 없음
  → 어깨, 허리 등 "천이 캐릭터에 붙어야 하는 부분"을
     검정(0)으로 페인팅해야 함

해결:
  1. Activate Cloth Paint
  2. 어깨/허리밴드 부분을 Shift+좌클릭으로 지우기 (= 검정 = 고정)
  3. Deactivate → Apply
  4. ☑ Max Distance 체크
```

### 문제 3: 천이 캐릭터 몸을 뚫는다

```
원인 (순서대로):

1. ☐ Physics Asset이 없음
   → SkeletalMesh에 Physics Asset 할당 확인
   → 없으면: 우클릭 → Create → Physics Asset

2. ☐ 관통 부위에 캡슐이 없음
   → Physics Asset 에디터 → 해당 본에 Add Body

3. ☐ 캡슐이 너무 작음
   → R키 (Scale) → 캡슐 키우기

4. ☐ Physics Type이 Simulated
   → Details → Physics Type → Kinematic으로 변경

5. ☐ 빠른 움직임에서만 관통
   → Iteration Count 올리기 (3→5→8)
   → 또는 Substep 올리기 (1→2)
```

### 문제 4: 천이 폭발하듯 튕긴다

```
원인:
  초기 포즈에서 캡슐과 천 메시가 심하게 겹침

해결:
  1. Physics Asset 에디터에서 겹치는 캡슐 크기 줄이기
  2. 또는 초기 포즈(T-Pose 등)에서 천과 캡슐이
     겹치지 않도록 조절
  3. Damping 값 올리기 (0.3~0.5) → 폭발적 움직임 감쇠
```

### 문제 5: 프레임이 떨어진다

```
원인:
  천 시뮬레이션 비용이 너무 높음

해결 (효과 큰 순서):
  1. Self Collision 끄기 → 가장 큰 절약
  2. Iteration/Substep 줄이기
  3. 파티클 수 줄이기 (Particle Distance 올리기)
  4. LOD 설정 → 원거리 시뮬 OFF
  5. stat Cloth로 비용 확인
```

## 8.2 증상별 상세 진단표

### 관통 관련

| 증상 | 원인 | 해결 | 난이도 |
|------|------|------|:------:|
| 특정 부위에서 관통 | 해당 본에 캡슐 없음 | 캡슐 추가 | 쉬움 |
| 전체적으로 관통 | Physics Asset 미연결 | 할당 확인 | 쉬움 |
| 빠른 동작에서만 관통 | Substep/Iteration 부족 | 값 올리기 | 쉬움 |
| 멀티레이어 관통 | Collision Thickness 부족 | 5mm 이상 | 중간 |
| 안쪽(몸 쪽) 관통 | Backstop 미설정 | Backstop 페인팅 | 중간 |
| 관절 부위 관통 | 캡슐 겹침/크기 | 캡슐 크기 조절 | 중간 |

### 움직임 관련

| 증상 | 원인 | 해결 | 난이도 |
|------|------|------|:------:|
| 천이 딱딱함 | Bend Stiffness 과다 | 값 줄이기 | 쉬움 |
| 천이 끝없이 흔들림 | Damping 부족 | 0.1~0.3으로 올리기 | 쉬움 |
| 천이 늘어남 | Iteration 부족 | Iteration 올리기 | 쉬움 |
| 바람에 과민 반응 | Drag/Lift 과다 | 값 줄이기 | 쉬움 |
| 천이 너무 가벼움 | Density 부족 | Density 올리기 | 쉬움 |
| 천이 중력 무시 | Density 과소 또는 Lift 과다 | Density 올리고 Lift 줄이기 | 쉬움 |

### 시스템 관련

| 증상 | 원인 | 해결 | 난이도 |
|------|------|------|:------:|
| 에디터 크래시 | 시뮬 중 Physics Asset 변경 | 시뮬 끄고 수정 | 쉬움 |
| 시뮬 중 갑자기 정지 | Physics Asset 불안정 | 시뮬 끄고 저장 후 재시작 | 쉬움 |
| 다른 UE 버전에서 안 됨 | 버전 간 API 변경 | 해당 버전 가이드 참고 | 중간 |
| Dataflow 노드 오류 | 노드 연결 잘못됨 | 예제 파일과 비교 | 중간 |

## 8.3 디버깅 도구 가이드

### 콘솔 명령어

```
` (백틱) 키로 콘솔 열기 후:

stat Cloth              → Cloth 시뮬레이션 성능 통계
stat Game               → 전체 게임 프레임 타임
p.Cloth.Visualize 1     → Cloth 파티클/노멀 시각화 (0으로 끄기)
```

### 에디터 시각화 옵션

```
SkeletalMesh 에디터 뷰포트:

Show → Clothing:
  ☑ Show Collision Volumes    → 캡슐/구체 와이어프레임
  ☑ Show Cloth Normals        → 천 노멀 방향 화살표
  ☑ Show Max Distance         → Max Distance 컬러맵
  ☑ Show Backstop             → Backstop 영역 시각화
```

### 테스트 체크리스트

반드시 다음 **5가지 동작**으로 테스트하세요:

| # | 테스트 | 확인 사항 |
|---|--------|----------|
| 1 | **T-Pose 정지** | 초기 안정성, 천이 자연스럽게 드레이핑 |
| 2 | **걷기** (Walk) | 일반 움직임에서 관통 없는지 |
| 3 | **달리기** (Run) | 빠른 움직임에서 관통/늘어남 |
| 4 | **180도 빠른 회전** | 천이 따라오는지, 폭발하지 않는지 |
| 5 | **바람 테스트** | Wind Source 추가 → 바람 반응 확인 |

## 8.4 자주 묻는 질문 (FAQ)

### Q: StaticMesh에 Cloth를 쓸 수 있나요?

**아니요.** Chaos Cloth는 SkeletalMesh 전용입니다. StaticMesh에 천 효과를 주려면:
- StaticMesh에 간단한 Armature(뼈대)를 추가하여 SkeletalMesh로 변환
- 또는 Blueprint에서 물리 시뮬레이션 사용 (별도 시스템)

### Q: 다른 캐릭터와 충돌할 수 있나요?

기본적으로 **같은 SkeletalMeshComponent 내 Physics Asset만** 참조합니다. 다른 액터와 충돌하려면 별도 설정이 필요하고 성능 비용이 높습니다.

### Q: Convex Hull을 왜 쓰면 안 되나요?

Chaos Cloth는 **Capsule/Sphere/Tapered Capsule**에 최적화되어 있습니다. Convex Hull은 충돌 계산이 불안정하여 관통, 떨림, 크래시를 유발할 수 있습니다.

### Q: 5.4 가이드를 5.7에서 따라해도 되나요?

**추천하지 않습니다.** Chaos Cloth는 버전마다 메뉴, 노드, 동작이 크게 변합니다. 반드시 자신의 UE 버전에 맞는 가이드를 참고하세요.

### Q: 시네마틱에서 더 높은 품질을 얻으려면?

실시간 한계를 넘는 품질이 필요하면:
1. Maya/Houdini에서 오프라인 시뮬레이션
2. 결과를 Joint에 베이크
3. UE로 Skeletal Animation으로 임포트
(9장 AAA 파이프라인 참조)

### Q: Self Collision 없이 치마 다리 관통을 막으려면?

완전한 해결은 어렵지만:
- **Backstop** 적극 활용
- **Buckling Stiffness** 높이기
- 다리 본에 **추가 캡슐** 배치 (크게)
- Max Distance를 다리 안쪽에서 제한

## 8.5 문제 해결 플로우차트

```
천이 이상하다!
│
├─ 아예 안 움직인다
│   ├─ 플러그인 켜져 있나? → NO → Edit → Plugins → 활성화
│   ├─ Apply Clothing Data 했나? → NO → 섹션 우클릭 → Apply
│   ├─ Max Distance 체크했나? → NO → Masks → ☑ Max Distance
│   └─ Max Distance > 0 영역 있나? → NO → 흰색으로 페인팅
│
├─ 바닥으로 떨어진다
│   └─ 고정 영역(검정)이 있나? → NO → 어깨/허리를 검정으로
│
├─ 몸을 뚫는다
│   ├─ Physics Asset 있나? → NO → 생성/할당
│   ├─ 해당 본에 캡슐? → NO → 캡슐 추가
│   ├─ 캡슐 크기 충분? → NO → 크기 키우기
│   ├─ Physics Type = Kinematic? → NO → 변경
│   └─ 빠른 동작에서만? → YES → Iteration/Substep 올리기
│
├─ 폭발/튕김
│   ├─ 초기 포즈에서 캡슐 겹침 → 캡슐 줄이기
│   └─ Damping 올리기 (0.3~0.5)
│
├─ 끝없이 흔들림
│   └─ Damping 올리기 (0.1~0.3)
│
├─ 너무 뻣뻣함
│   └─ Bend Stiffness 줄이기
│
├─ 성능 문제
│   ├─ stat Cloth로 비용 확인
│   ├─ Self Collision 끄기
│   ├─ Iteration/Substep 줄이기
│   ├─ 파티클 수 줄이기
│   └─ LOD 설정 확인
│
└─ 에디터 크래시
    ├─ 시뮬 끄고 저장
    ├─ 최신 패치 설치
    └─ 시뮬 중 Physics Asset 수정 금지!
```

## 체크리스트

- [ ] 가장 흔한 5가지 문제와 해결법 숙지
- [ ] stat Cloth 명령어로 성능 확인 가능
- [ ] Show Collision Volumes로 충돌 디버깅 가능
- [ ] 5가지 테스트 동작(정지, 걷기, 달리기, 회전, 바람) 수행

---
[← 이전: 성능 최적화](07-Performance-Optimization.md) | [다음: AAA 프로덕션 파이프라인 →](09-AAA-Production-Pipeline.md)
