# /inspect-sim — Simulation 진단 에이전트 호출

Groom 헤어 / Chaos Cloth / Physics Asset / KawaiiPhysics 의 **현재 파라미터 진단** + UE 5.7 공식 소스 대조.

## 호출 형식

사용자 발화 예:
- `/inspect-sim PC_01 Sanjuk 헤어가 뻣뻣해`
- `/inspect-sim 옷이 메시 관통 — Chaos Cloth 진단`
- `/inspect-sim PC_01 Physics Asset 캡슐 콜리전 검증`

## 실행 지침

Agent tool 의 `subagent_type=sim-inspector` 로 호출. prompt 에 포함:

1. **자산 경로**: Groom asset / Cloth asset / Physics Asset
2. **현재 작업 컨텍스트**: 메모리 [[pc01-hair-gravity-bug]] 같은 진행 상태
3. **호소 내용**: 사용자 발화 그대로 (시각/체감 표현 중요)
4. **선행 메모리**: [[reference-groom-physics-params]] (CosseratRods 솔버), [[reference-kawaii-physics]]
5. **물리 cache**: cache/ue57_groom/, cache/kawaii_physics/

## 에이전트가 반환할 형식

진단 보고 + 처방 spec. 일반적으로 그룹별 파라미터 (Gravity / BendStiffness / RadialDamping 등) 권장값.

## 사용 안 할 때

- 단순 파라미터 값 dump → `Bash` 로 dump_pc01_hair_active_full.py 등 직접
- ABP 영역 (애니메이션 / IK / 리그) → `/inspect-abp` 사용

## 관련 메모리

- [[reference-sanjuk-agents]]
- [[reference-groom-physics-params]] — Groom CosseratRods 솔버 단일 진실원
- [[feedback-project-collision-requires-physassets-review]] — ProjectCollision=True 함정
- [[pc01-hair-gravity-bug]] — 현재 PC_01 헤어 튜닝 상태
