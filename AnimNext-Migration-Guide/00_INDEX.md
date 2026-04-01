# SandboxCharacter_CMC_ABP → AnimNext(UAF) 변환 가이드

## 문서 목차

이 가이드는 기존 Animation Blueprint(ABP)를 Unreal Engine 5.7의 차세대 애니메이션 시스템인
**AnimNext (UAF: Unreal Animation Framework)**로 변환하는 전체 과정을 다룹니다.

> **대상 독자**: UE5 애니메이션 시스템에 대한 기초 지식이 있는 개발자
> **프로젝트**: MonolithTest (UE 5.7)
> **원본 에셋**: `/Game/Blueprints/SandboxCharacter_CMC_ABP`

---

### 문서 구성

| 순서 | 파일 | 내용 |
|------|------|------|
| 01 | [현재 ABP 분석](./01_CURRENT_ABP_ANALYSIS.md) | 변환 대상인 기존 ABP의 구조 완전 분석 |
| 02 | [AnimNext(UAF) 개념 이해](./02_ANIMNEXT_CONCEPTS.md) | UAF의 핵심 개념과 ABP와의 차이점 |
| 03 | [사전 준비](./03_PREREQUISITES.md) | 플러그인 활성화, 프로젝트 설정, 폴더 구조 |
| 04 | [Workspace & System 생성](./04_WORKSPACE_AND_SYSTEM.md) | UAF의 최상위 에셋 생성 |
| 05 | [Data Interface 구성](./05_DATA_INTERFACE.md) | 변수 시스템을 Data Interface로 변환 |
| 06 | [Animation Graph 구축](./06_ANIMATION_GRAPH.md) | TraitStack 기반 AnimGraph 재구성 |
| 07 | [Chooser + Motion Matching](./07_CHOOSER_AND_MOTION_MATCHING.md) | State Machine을 데이터 기반 시스템으로 대체 |
| 08 | [Module 작성](./08_MODULES.md) | 로직 함수를 UAF Module로 이전 |
| 09 | [Character BP 연결](./09_CHARACTER_INTEGRATION.md) | AnimNextComponent 설정 및 캐릭터 연결 |
| 10 | [디버깅 & 검증](./10_DEBUGGING_AND_VALIDATION.md) | 문제 해결, 디버깅 도구, 검증 체크리스트 |
| 11 | [UAF 에셋 마이그레이션 로그](./11_UAF_ASSET_MIGRATION_LOG.md) | UEFN_Mannequin UAF 폴더 생성 작업 기록 |
| 부록A | [용어 사전](./APPENDIX_A_GLOSSARY.md) | ABP ↔ UAF 용어 대응표 |
| 부록B | [참고 자료](./APPENDIX_B_REFERENCES.md) | 공식 문서, 커뮤니티 리소스 링크 |

---

### 변환 작업 흐름 요약

```
Phase 0: 사전 준비                              [완료]
  ├── 플러그인 활성화, 폴더 구조 생성
  └── UAF 에셋 마이그레이션 (11장 참조)
      ├── PoseSearch Schema 27개 생성            [완료]
      ├── PoseSearch Database 99개 생성          [완료 - 시퀀스 연결 필요]
      ├── BlendSpace/AimOffset 7개 생성          [완료 - 샘플 포함]
      ├── AnimBlueprint 2개 생성                 [완료]
      └── Material/MI 4개 생성                   [완료]

Phase 1: 기반 구축                              [미착수]
  ├── Workspace 생성
  ├── System 생성
  └── Data Interface 정의

Phase 2: 애니메이션 파이프라인                    [미착수]
  ├── Animation Graph (TraitStack) 구축
  ├── Motion Matching 노드 설정
  └── Chooser Table 구성

Phase 3: 로직 이전                              [미착수]
  ├── Module 작성 (업데이트 로직)
  └── 보조 시스템 이전 (AO, Lean, Foot Placement)

Phase 4: 통합 & 검증                            [미착수]
  ├── Character BP에 AnimNextComponent 추가
  ├── 기존 ABP와 비교 검증
  └── 성능 프로파일링
```

---

### 주의사항

1. **UAF는 UE 5.7 기준 Experimental** - 프로덕션 사용 비권장
2. **기존 ABP를 삭제하지 마세요** - 별도 테스트 캐릭터에서 작업
3. **버전 간 호환성 미보장** - UE 업데이트 시 API 변경 가능
4. **UE 5.8에서 첫 공식 데모 예정** - Game Animation Sample에 UAF 캐릭터 포함

---

*생성일: 2026-03-28*
*UE 버전: 5.7*
*원본 ABP: SandboxCharacter_CMC_ABP*
