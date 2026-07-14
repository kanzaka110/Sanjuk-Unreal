# 렛지(Ledge) 시스템 엔지니어 요청사항 — 2026-07-14

요청자: 애니메이션 TA (PC_01 렛지 핸드IK 작업 중 발견)
대상: 렛지 무브먼트 담당 엔지니어

## 요약

| # | 항목 | 심각도 | 요청 |
|---|------|--------|------|
| 1 | Move→Idle 전환이 애님 안무를 절단 | 높음 (모션 품질) | 전환 타이밍을 애님 기준으로 동기화 |
| 2 | BP_EM_Ledge 컴파일 시 에디터 크래시 | 높음 (작업 안정성) | SBZoneEnvActor::BeginPlay 널참조 수정 |
| 3 | FSBLedgeMoveData 런타임 접근성 | 낮음 (편의) | 파라미터 BP/Python 노출 |

---

## 1. Move→Idle 전환이 이동 애님 안무를 절단함

### 증상
렛지 한 칸 이동 시 이동 애님(예: `P_Player_Ledge_Move_ShortL_Wallless`)이 끝까지 재생되지 않고 Idle로 잘림. 후행 손의 재그립 동작이 잘려나가 도착부 손 모션이 부자연스러움.

### 실측 근거 (2026-07-13~14)
- `FSBLedgeMoveData.unit_duration = 0.4s` 시점에 캡슐 정지 + Idle 전환 요청
- 그러나 이동 애님의 손 안무는 **0.55s까지** 걸쳐 있음:

```
P_Player_Ledge_Move_ShortL_Wallless (AnimPose 프레임 샘플링 + 베이크 커브 실측)
  왼손 릴리즈→재그립 : 0.067 ~ 0.37s   (스윙 속도 220~270cm/s)
  오른손 릴리즈→재그립: 0.267 ~ 0.53s   ← 0.4s 컷에 후반부 절단
```

- 절단 부작용 실측: 오른손이 스윙 중간에 Idle 블렌드로 낚아채짐, 펠비스 정착 꼬리 압축(약 19cm 낙차가 짧은 블렌드로 압축 → 홀딩 딥)
- unit_duration은 이동 속도 전용이라 애님과 독립 (0.6/1.5로 늘리면 애님은 완주하지만 이동이 느려져 게임 필 훼손 — 기각). RateScale 매칭도 모션 속도감 이상으로 기각

### 요청
Move→Idle 전환을 unit_duration 만료가 아니라 **애님 이동 페이즈 종료(또는 애님 노티파이/커브 신호)와 동기화**해 주세요. 대안: 전환 요청 후에도 현재 이동 애님이 완주(또는 지정 블렌드 포인트 도달)할 때까지 Idle 스위치를 지연.

(대안 경로로 애니메이터 리타이밍(이동 페이즈 0.6→0.4s 키 재배치)도 가능하지만, 전 렛지 이동 애님 수정이 필요해 코드 동기화가 정석이라 판단)

---

## 2. BP_EM_Ledge 컴파일 → 에디터 즉사 크래시

### 증상
`BP_EM_Ledge`(부모 `SBZoneEnvActor`)를 에디터에서 **컴파일**하면 리인스턴싱 중 크래시. 2026-07-13 2회 재현.

### 콜스택 요지
- 리인스턴싱 BeginPlay 경로에서 `SBZoneEnvActor.cpp:467` 널참조 (ACCESS_VIOLATION)
- 인스턴스 값 수정(디테일 패널)은 안전, **컴파일만** 위험

### 요청
`SBZoneEnvActor::BeginPlay` (라인 467 부근) 널 가드 추가. TA/디자이너가 렛지 액터 BP를 만졌다가 컴파일 한 번에 에디터가 죽는 상태라 작업 위험도가 높습니다.

---

## 3. (편의) FSBLedgeMoveData 파라미터 노출

- `unit_duration` / `unit_size` / `capsule_z_offset` 등이 C++ 전용이라 런타임 오버라이드/Python 접근 불가 (`ledge_move_data` 프로퍼티 미노출, CMC는 `call_method("GetLedgeMoveData")` 우회 필요)
- 튜닝 이터레이션 속도를 위해 BlueprintReadWrite 또는 에디터 노출 요청 (1번이 해결되면 우선순위 낮음)

---

## 참고: 현재 TA측 대응 상태
- ABP에 핸드IK 시스템 구축 완료 (시퀀스 커브 기반, 도착지 Idle 손위치 고정) — 절단 증상을 런타임 보정으로 최대한 마스킹 중이나, 1번이 해결되어야 후행 손 재그립 모션이 원본대로 나옴
- 애님 166종에 `ledge_hand_ik_l/r` 커브 베이크 완료 (AnimationModifier `AM_SBLedgeHandIK`)
