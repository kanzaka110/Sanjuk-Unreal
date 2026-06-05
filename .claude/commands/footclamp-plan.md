# /footclamp-plan — PC_01 경사 발별 비대칭 clamp 작업 복원

다음주 작업 "PC_01_CtrlRig_FootClamp 경사 위/아래 발 ankle clamp 비대칭화" 컨텍스트를 한 번에 복원하고 시작 지점으로 안내.

## 실행 순서

### 1단계: 계획 메모리 로드

```
Read ~/.claude/projects/C--Dev-Sanjuk-Unreal/memory/project_pc01_footclamp_asymmetric_plan.md
```
실측 데이터 표(BoneNames / Pitch·Yaw·Roll clamp / CombatAlpha 로직) + 전략 STEP A~C + 권장 수치 + 리스크를 사용자에게 압축 요약.

### 2단계: 환경 점검 (병렬)

```bash
curl -s -m 2 -o /dev/null -w "%{http_code}" http://localhost:9316/mcp   # Monolith
```
- ✅ → 에셋 실측/검증 가능 (단 그래프 add_node 는 크래시 위험, 읽기 전용)
- ❌ → `/recover` 안내, 메모리 기반 설계만 진행

### 3단계: 에셋 현재값 재확인 (Monolith 살아있을 때, 선택)

메모리 값은 2026-06-05 실측. 그새 변경됐을 수 있으니 재확인 권장:
```
blueprint_query.get_cdo_properties(
  asset_path="/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_FootClamp",
  property_names=["BoneNames","Angle_Clamp_Pitch","Angle_Clamp_Yaw","Angle_Clamp_Roll","CombatEnterDelay"])
```
메모리 값과 diff → 바뀌었으면 메모리 갱신 먼저.

⚠ 경로 단일 슬래시 필수([[feedback-monolith-path-double-slash-fatal]]). `get_control_rig_graph` 전체 덤프(66KB)는 토큰 폭발 → 필요시 서브에이전트로 슬라이스 분석.

### 4단계: 시작 갈래 제시

사용자에게 두 갈래 중 선택 요청:
1. **부호/축 확정 먼저** — PIE 경사 레벨에서 foot_l/foot_r Euler 실축 → YXZ 어느 축·부호가 오르막/내리막에 대응하는지 확정 (수치 단정 전 권장 순서)
2. **노드 설계도 바로** — STEP A~C 핀 단위 배선도 작성 → 에디터 수동 구현

## 작업 원칙 (재확인)

- **에셋 그래프 변경 = 사용자 승인 후 + P4 체크아웃 선행.**
- Control Rig 그래프 노드 추가는 **에디터 수동** (Monolith add_control_rig_node VariableGet 크래시 이력).
- 권장 Loose 수치는 ⚠ 제안치 — PIE 관찰 후 튜닝. 부호는 실축 후 확정.

## 관련 메모리

- [[project-pc01-footclamp-asymmetric-plan]] — 본 작업 메인
- [[reference-foot-placement-source-5-7]] — FootPlacement 노드 ground truth (clamp 릭과 별개 레이어)
- [[feedback-monolith-controlrig-addnode-crash]] — 그래프 편집 위험
