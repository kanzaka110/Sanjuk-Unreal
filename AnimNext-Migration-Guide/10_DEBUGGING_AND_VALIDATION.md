# 10. 디버깅 & 검증

[← 이전: Character BP 연결](./09_CHARACTER_INTEGRATION.md) | [목차](./00_INDEX.md) | [부록A: 용어 사전 →](./APPENDIX_A_GLOSSARY.md)

---

## 10.1 개요

UAF 변환이 완료되었으면, 기존 ABP와의 동작 일치 여부를 검증하고
성능 개선을 확인해야 합니다.

---

## 10.2 시각적 검증

### 나란히 비교 테스트

테스트 레벨에 기존 ABP 캐릭터와 UAF 캐릭터를 나란히 배치하여 비교합니다.

```
┌─────────────────────────────────────────────────────┐
│                   테스트 레벨                         │
│                                                      │
│   [ABP 캐릭터]              [UAF 캐릭터]             │
│   BP_SandboxCharacter       BP_TestCharacter_UAF     │
│                                                      │
│   둘 다 같은 입력을 받도록 설정                       │
│   → 같은 애니메이션이 재생되는지 비교                 │
└─────────────────────────────────────────────────────┘
```

### 검증 시나리오 체크리스트

각 시나리오에서 ABP와 UAF의 동작을 비교합니다:

#### 기본 이동

| # | 시나리오 | 확인 사항 | ABP | UAF |
|---|---------|----------|-----|-----|
| 1 | 정지 상태 | Idle 애니메이션 재생 | ☐ | ☐ |
| 2 | 전방 걷기 | Walk Forward 애니메이션 | ☐ | ☐ |
| 3 | 전방 달리기 | Run Forward 애니메이션 | ☐ | ☐ |
| 4 | 스프린트 | Sprint 애니메이션 | ☐ | ☐ |
| 5 | 정지 → 이동 | 출발 전환이 자연스러운가 | ☐ | ☐ |
| 6 | 이동 → 정지 | 정지 전환이 자연스러운가 | ☐ | ☐ |
| 7 | 좌/우 스트레이프 | 측면 이동 애니메이션 | ☐ | ☐ |
| 8 | 후방 이동 | 후진 애니메이션 | ☐ | ☐ |

#### 방향 전환

| # | 시나리오 | 확인 사항 | ABP | UAF |
|---|---------|----------|-----|-----|
| 9 | 180도 방향 전환 | 피벗 애니메이션 | ☐ | ☐ |
| 10 | 90도 방향 전환 | 부드러운 전환 | ☐ | ☐ |
| 11 | 제자리 회전 | Turn In Place 발동 | ☐ | ☐ |
| 12 | 연속 방향 전환 | 떨림 없이 부드러운가 | ☐ | ☐ |

#### 공중 동작

| # | 시나리오 | 확인 사항 | ABP | UAF |
|---|---------|----------|-----|-----|
| 13 | 점프 | Jump Start → Fall Loop | ☐ | ☐ |
| 14 | 가벼운 착지 | Light Land 애니메이션 | ☐ | ☐ |
| 15 | 무거운 착지 | Heavy Land 애니메이션 | ☐ | ☐ |
| 16 | 이동 중 착지 | Moving Land 전환 | ☐ | ☐ |
| 17 | 절벽 낙하 | Fall → Land 전환 | ☐ | ☐ |

#### 보조 시스템

| # | 시나리오 | 확인 사항 | ABP | UAF |
|---|---------|----------|-----|-----|
| 18 | Aim Offset | 마우스 이동 시 상체 회전 | ☐ | ☐ |
| 19 | 기울기 (Lean) | 방향 전환 시 몸 기울기 | ☐ | ☐ |
| 20 | Foot Placement | 경사면에서 발 IK | ☐ | ☐ |
| 21 | 계단 발 배치 | 계단에서 올바른 발 위치 | ☐ | ☐ |
| 22 | Idle Break | 장시간 정지 시 모션 | ☐ | ☐ |

---

## 10.3 UAF 디버깅 도구

### Output Log 확인

1. **Window → Developer Tools → Output Log** 열기

2. AnimNext 관련 로그 필터링:
   ```
   LogAnimNext
   LogPoseSearch
   LogChooser
   ```

3. 주요 로그 메시지:

| 로그 | 의미 |
|------|------|
| `AnimNextComponent activated` | 컴포넌트 정상 활성화 |
| `Workspace loaded: WS_*` | Workspace 로드 성공 |
| `No valid database found` | Chooser가 DB를 찾지 못함 |
| `Pose search cost: X.XX` | MM 검색 비용 (낮을수록 좋음) |
| `TraitStack evaluation: Xms` | TraitStack 평가 시간 |

### Monolith MCP를 통한 디버깅

프로젝트에 Monolith MCP가 연결되어 있으므로 다음을 활용할 수 있습니다:

```
# ABP 정보 조회
animation_query: get_abp_info
  → 상태 머신, 그래프, 변수 확인

# 빌드 오류 확인
editor_query: get_build_errors
  → 컴파일 오류 확인

# 로그 실시간 확인
editor_query: tail_log
  → AnimNext 관련 로그 모니터링
```

### Visual Logger

1. **Window → Developer Tools → Visual Logger** 열기

2. 기록 시작 (Record 버튼)

3. 시나리오 실행 후 기록 분석:
   - Pose Search 궤적 시각화
   - 선택된 애니메이션 확인
   - 블렌드 가중치 확인

### Animation Insights (UE 5.7)

1. **Window → Developer Tools → Animation Insights** (있는 경우)

2. 또는 **콘솔 명령어**:
   ```
   ShowDebug Animation
   ```

3. 화면에 표시되는 정보:
   - 현재 재생 중인 애니메이션
   - 블렌드 가중치
   - Motion Matching 검색 결과

---

## 10.4 성능 프로파일링

### 프로파일링 방법

#### Unreal Insights

1. **콘솔 명령어**:
   ```
   stat AnimNext
   stat PoseSearch
   ```

2. 또는 **Unreal Insights** 도구:
   ```
   {프로젝트경로}/Binaries/Win64/UnrealEditor.exe -trace=default,animation
   ```

#### 주요 측정 지표

| 지표 | ABP 예상값 | UAF 예상값 | 측정 방법 |
|------|----------|----------|----------|
| **AnimGameThreadTime** | X ms | ~0 ms | `stat Animation` |
| **총 애니메이션 시간** | X ms | < X ms | `stat AnimNext` |
| **Pose Search 시간** | X ms | X ms (유사) | `stat PoseSearch` |
| **메모리 사용** | X MB | < X MB | `stat Memory` |

#### stat 명령어 모음

```
stat Animation          ← 기존 ABP 애니메이션 통계
stat AnimNext           ← UAF 통계 (있는 경우)
stat PoseSearch         ← Motion Matching 통계
stat Game               ← 전체 게임 스레드 시간
stat Threading          ← 스레드별 시간
stat Unit               ← 프레임 시간 요약
```

### 비교 테스트 절차

1. **기존 ABP 캐릭터로 프로파일링**
   ```
   1. ABP 캐릭터만 레벨에 배치
   2. stat Animation 활성화
   3. 동일한 시나리오 실행 (30초)
   4. AnimGameThreadTime 기록
   5. 스크린샷 저장
   ```

2. **UAF 캐릭터로 프로파일링**
   ```
   1. UAF 캐릭터만 레벨에 배치
   2. stat AnimNext 활성화
   3. 동일한 시나리오 실행 (30초)
   4. 애니메이션 관련 시간 기록
   5. 스크린샷 저장
   ```

3. **결과 비교**

---

## 10.5 일반적인 문제와 해결 방법

### 문제 1: 캐릭터가 T-Pose

```
원인 진단 순서:
1. AnimNextComponent가 존재하는가?
   → Components 패널 확인
2. Workspace가 할당되었는가?
   → AnimNextComponent → Workspace 프로퍼티
3. SkeletalMeshComponent Animation Mode = "No Animation"인가?
   → "Use Animation Blueprint"면 UAF 비활성화됨
4. System이 실행되는가?
   → Output Log에서 AnimNext 로그 확인
5. Animation Graph에 유효한 Trait가 있는가?
   → AG_SandboxCharacter 그래프 확인
```

### 문제 2: 애니메이션이 재생되지만 이상함

```
원인 진단:
1. Chooser Table이 올바른 DB를 반환하는가?
   → Chooser 에디터에서 조건 확인
2. Pose Search DB에 충분한 시퀀스가 있는가?
   → DB 에디터에서 시퀀스 목록 확인
3. 궤적 데이터가 올바른가?
   → Visual Logger로 궤적 시각화
4. Data Interface 값이 정확한가?
   → Module에서 Print/Log 노드로 값 출력
```

### 문제 3: Aim Offset이 작동하지 않음

```
원인 진단:
1. Module에서 AO 값이 계산되는가?
   → EnableAO, AO_Yaw, AO_Pitch 값 확인
2. Aim Offset Trait의 Alpha가 0이 아닌가?
   → Workspace 변수 EnableAO 확인
3. BS_Neutral_AO_Stand 에셋이 올바르게 참조되는가?
   → Trait의 Asset 프로퍼티 확인
```

### 문제 4: Foot Placement가 이상함

```
원인 진단:
1. Foot Placement Trait가 활성화되었는가?
   → AllowFootPinning 값 확인
2. PlantSettings가 올바른가?
   → Workspace 변수의 FootPlacementPlantSettings 확인
3. 지면 트레이스가 작동하는가?
   → 콜리전 설정 확인
```

### 문제 5: 에디터 크래시

```
대처:
1. Saved/Logs/ 폴더에서 최신 로그 파일 확인
2. 크래시 직전의 작업 식별
3. 알려진 크래시 원인:
   - Workspace 에디터에서 자식 노드 더블클릭
   - 순환 참조가 있는 Module
   - 잘못된 Trait 파라미터 타입
4. 에디터 재시작 후 안전한 조작으로 재시도
```

---

## 10.6 최종 검증 체크리스트

### 기능 검증

- [ ] Idle 포즈가 올바름
- [ ] 걷기/달리기/스프린트 전환 정상
- [ ] 방향 전환 (피벗) 자연스러움
- [ ] 점프/낙하/착지 전환 정상
- [ ] Aim Offset 작동
- [ ] Lean (기울기) 작동
- [ ] Foot Placement (발 IK) 작동
- [ ] Idle Break 발동
- [ ] 제자리 회전 (Turn In Place) 작동

### 성능 검증

- [ ] AnimGameThreadTime 감소 확인
- [ ] 전체 프레임 시간 개선 또는 유지
- [ ] 메모리 사용량 확인
- [ ] 다수 캐릭터 (10+) 테스트

### 안정성 검증

- [ ] 30분 이상 플레이 시 크래시 없음
- [ ] 빠른 입력 전환 시 떨림 없음
- [ ] 극단적 상황 (높은 곳 낙하, 벽 충돌) 시 안정적
- [ ] PIE 반복 시작/중지 시 안정적

---

## 10.7 변환 전후 비교 요약

### 구조 비교

| 항목 | ABP (기존) | UAF (변환 후) |
|------|-----------|-------------|
| 에셋 수 | 1 (ABP) | 4 (Workspace, System, Module, Graph) |
| 변수 수 | 76개 | ~25개 (67% 감소) |
| 함수 수 | 59개 | Module 내 ~5개 섹션 (92% 감소) |
| 그래프 노드 | ~954개 | ~93개 (90% 감소) |
| State Machine | 7상태, 22트랜지션 | Chooser Table 1개 |
| AnimGraph 노드 | 22개 | 7 Traits |

### 코드 복잡도

| 측면 | ABP | UAF |
|------|-----|-----|
| 데이터 전달 | 수동 (Cast + Set) | 자동 (Data Interface) |
| 상태 전환 | 수동 와이어링 | 선언적 테이블 |
| 블렌딩 | 수동 블렌드 노드 | 자동 (MM + TraitStack) |
| 스레딩 | 제한적 | 완전 멀티스레드 |
| 확장성 | 노드 추가 → 복잡도 증가 | Trait 추가 → 독립적 |

---

[← 이전: Character BP 연결](./09_CHARACTER_INTEGRATION.md) | [목차](./00_INDEX.md) | [부록A: 용어 사전 →](./APPENDIX_A_GLOSSARY.md)
