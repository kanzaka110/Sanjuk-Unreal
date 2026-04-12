# 애니메이션 작업 시작 체크리스트

애니메이션 관련 작업을 시작할 때 환경과 에셋 상태를 점검하는 명령어.

## 입력

사용자가 제공하는 정보 (선택):
- 작업 대상 캐릭터 / 스켈레톤
- 작업 유형 (몽타주, 블렌드스페이스, ABP, 리타겟 등)

## 실행 순서

### 1단계: MCP 연결 확인

Monolith 연결 상태 빠른 확인 (연결 안 되면 중단 + 안내)

### 2단계: 애니메이션 에셋 현황 조회

Monolith를 사용하여:

1. **스켈레톤 목록** 조회 — 프로젝트 내 사용 가능한 스켈레톤
2. **AnimBlueprint 목록** — 현재 ABP 구성 확인
3. **AnimSequence 목록** — 사용 가능한 클립 현황
4. **AnimMontage 목록** — 기존 몽타주 확인
5. **BlendSpace 목록** — 기존 블렌드스페이스 확인

### 3단계: 작업 유형별 체크리스트

**몽타주 작업 시:**
- [ ] 대상 AnimSequence 존재 확인
- [ ] Slot 설정 확인 (DefaultSlot / UpperBody)
- [ ] Section 분할 계획 (Windup → Strike → Recovery)
- [ ] Notify 계획 (사운드, 이펙트, 판정)

**블렌드스페이스 작업 시:**
- [ ] 축 파라미터 결정 (Speed, Direction, AimPitch 등)
- [ ] 입력 AnimSequence 준비 상태
- [ ] 1D vs 2D vs Aim Offset 결정

**ABP/State Machine 작업 시:**
- [ ] State 목록 정의 (Idle, Walk, Jog, Sprint...)
- [ ] Transition 조건 정의 (Speed 임계값 등)
- [ ] AnimCurve 피드백 구성

**리타겟 작업 시:**
- [ ] 소스/타겟 스켈레톤 확인
- [ ] IK Retargeter 에셋 존재 확인
- [ ] 본 매핑 체인 설정 상태

### 4단계: 작업 플랜 출력

점검 결과 기반으로 작업 순서 제안:
1. 필요한 에셋 생성/수정 순서
2. Monolith 액션 시퀀스
3. 예상 검증 방법
