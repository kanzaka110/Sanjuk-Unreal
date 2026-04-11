# 9. AAA 프로덕션 파이프라인

> 이 장은 중급~고급 내용입니다. 3~5장의 기본을 먼저 익히고 진행하세요.

## 9.1 전체 워크플로우

AAA 게임에서 Chaos Cloth를 사용하는 프로덕션 파이프라인입니다.

```
[1. 모델링 — DCC 도구]
Marvelous Designer / CLO3D
├── 의류 패턴 디자인
├── 물리 속성 설정 (Stiffness, Thickness 등)
└── USD 또는 FBX로 익스포트 (물리 속성 포함 가능)
         │
         ↓
[2. 리깅 — Maya / Blender]
├── Sim Mesh 리깅 (저해상도)
├── Render Mesh 리깅 (고해상도)
├── 두 메시 모두 같은 스켈레톤에 바인딩
└── FBX 익스포트
         │
         ↓
[3. UE5 셋업 — Chaos Cloth]
├── Cloth Asset 생성 (Clothing Tool 또는 Dataflow)
├── Max Distance / Backstop 페인팅
├── 콜리전 세트 구성 (격리된 캡슐)
├── 파라미터 튜닝
└── LOD 설정 (3단계)
         │
         ↓
[4. 검증 & 최적화]
├── 다양한 애니메이션으로 테스트 (5가지 동작)
├── stat Cloth 프로파일링
├── 멀티 플랫폼 확인 (PC/콘솔)
└── QA 피드백 → 2~3단계 반복
```

## 9.2 DCC에서 UE로: 물리 속성 전달

### Marvelous Designer → UE5 (USD)

Marvelous Designer에서 USD 익스포트 시 물리 속성을 포함할 수 있습니다.
Chaos Cloth Dataflow에서 **USDImport 노드**로 가져오면 속성이 자동 전달됩니다.

### 단위 변환 테이블

| 속성 | Marvelous Designer | Unreal Engine | 변환 방법 |
|------|:------------------:|:-------------:|----------|
| Bending Stiffness | g·mm²/s² | kg·cm²/s² | ÷ 100,000 |
| Stretch Stiffness | g/s² | kg/s² | ÷ 1,000 |
| Weight (GSM) | g/m² | Density | 환산 필요 |
| Thickness | mm | cm | ÷ 10 |

### 변환 예시

```
MD에서 Bending Stiffness = 6000 g·mm²/s²
→ UE에서 = 6000 ÷ 100000 = 0.06 kg·cm²/s²

MD에서 Thickness = 5mm
→ UE에서 = 5 ÷ 10 = 0.5cm
```

### FBX 워크플로우 주의사항

| 주의 | 설명 |
|------|------|
| 스켈레톤 포함 | 두 메시 모두 같은 스켈레톤에 바인딩 |
| 스케일 통일 | DCC와 UE의 스케일 팩터 확인 (UE: 1단위 = 1cm) |
| UV 정리 | 겹치는 UV 없도록 |
| 메시 원점 | 캐릭터 루트에 맞추기 |
| 삼각형 OK | 쿼드 변환 불필요 |

## 9.3 Panel Cloth (Dataflow) 상세 가이드

AAA 프로덕션에서는 기본 Clothing Tool 대신 **Panel Cloth (Dataflow)**를 사용합니다.

### Dataflow 기본 노드 구성

```
┌──────────────┐     ┌──────────────┐     ┌─────────────────┐
│ USD Import   │     │ WeightMap    │     │ Simulation      │
│ 또는         │ ──→ │ MaxDistance  │ ──→ │ SolveConfig     │
│ StaticMesh   │     │ (페인팅)     │     │ Lod0            │
│ Import       │     └──────────────┘     │ (파라미터 설정)  │
└──────────────┘              │            └─────────────────┘
                              ↓
                     ┌──────────────┐
                     │ PhysicsAsset │
                     │ 또는         │
                     │ Kinematic    │
                     │ Collider     │
                     └──────────────┘
```

### 주요 노드 설명

| 노드 | 역할 |
|------|------|
| **USDImport / StaticMeshImport** | DCC에서 만든 메시 가져오기 |
| **DeleteElement** | 불필요한 메시 제거 |
| **MergeClothCollection** | 여러 메시를 하나로 통합 |
| **WeightMap_MaxDistance** | Max Distance 페인팅 (2D/3D 뷰) |
| **WeightMap_Backstop** | Backstop 페인팅 |
| **SimulationSolveConfigLod0** | 시뮬레이션 파라미터 설정 |
| **PhysicsAsset** | Physics Asset 기반 충돌 |
| **KinematicCollider** | Static Mesh 기반 정밀 충돌 |
| **Remesh** | LOD용 메시 밀도 감소 |

### Dataflow의 장점

| 장점 | 설명 |
|------|------|
| 노드 조합 자유 | 복잡한 워크플로우를 시각적으로 구성 |
| LOD 자동화 | Remesh 노드로 LOD 메시 자동 생성 |
| DCC 연동 | USD 직접 임포트 + 물리 속성 전달 |
| 멀티레이어 | Outfit Asset과 통합 |
| 재사용 | 노드 그래프를 템플릿으로 복사 |

## 9.4 Baked Animation 기법

실시간으로 불가능한 복잡한 천 동작은 **오프라인 시뮬 후 베이크**합니다.

### 사용 사례

| 상황 | 예시 |
|------|------|
| 토폴로지 변경 | 후드 벗기/쓰기 |
| 극적 연출 | 망토 펼침, 드레스 회전 |
| 정밀 상호작용 | 손으로 옷을 잡는 동작 |
| 시네마틱 | 최고 품질이 필요한 장면 |

### 워크플로우

```
[Maya Ncloth / Houdini Vellum]
├── 고품질 오프라인 시뮬레이션 실행
├── Constraint, Goal로 정밀 제어
├── 시뮬 결과를 Joint에 베이크
└── Skeletal Animation으로 FBX 익스포트
         ↓
[UE5]
├── Skeletal Animation으로 임포트
├── Animation Sequence에서 재생
└── 실시간 Cloth 시뮬과 블렌딩 가능
```

### 실시간 ↔ 베이크 블렌딩

```
시네마틱:
[베이크 애니메이션] ──→ (블렌딩 0.5~1초) ──→ [실시간 시뮬레이션]
  후드 벗는 정밀 동작        부드러운 전환         이후 자유 움직임
```

## 9.5 팀 워크플로우

| 역할 | 담당 | 산출물 |
|------|------|--------|
| 캐릭터 아티스트 | 모델링, UV, Sim/Render 분리 | FBX/USD |
| 리거 | 스켈레톤 바인딩, 기본 Physics Asset | Physics Asset |
| 테크니컬 아티스트 | Cloth 파라미터, 콜리전, LOD | Cloth Asset |
| 애니메이터 | 베이크 애니메이션, 피드백 | AnimSequence |
| QA | 관통/성능 테스트 | 버그 리포트 |

## 9.6 MCP 도구 활용

Claude Code와 MCP를 사용하면 일부 작업을 자동화할 수 있습니다.

| MCP | 가능한 작업 |
|-----|-----------|
| **Monolith** | Physics Asset 바디 조회/수정, 컨스트레인트 설정 |
| **runreal** | Physics Asset 배치 할당, 자동화 스크립트 |
| **ChiR24/Unreal_mcp** | Chaos Cloth 설정 직접 제어 (유일한 MCP) |

### Monolith 활용 예시

```
"SK_Character의 Physics Asset을 분석해줘.
 바디 수, 본 매핑, 컨스트레인트를 보여줘"

"spine_03 바디를 Kinematic으로 변경하고
 Collision Preset을 Cloth용으로 설정해줘"
```

## 체크리스트

- [ ] DCC → UE 워크플로우 이해
- [ ] 단위 변환 테이블 참조 가능
- [ ] Panel Cloth (Dataflow) 기본 노드 이해
- [ ] Baked Animation 기법 이해
- [ ] MCP 도구 활용 방법 인지

---
[← 이전: 트러블슈팅](08-Troubleshooting.md) | [다음: 참고 자료 →](10-References.md)
