# [협의 요청] NPC_100 드론 — 프록시 캡슐 위치를 BP 연출이 제어할 방법 필요

작성: 2026-07-23, 애니메이션 TA. 대상: SB 캐릭터/네트워크 프로그래밍팀.

## 요약

`NPC_100_Body_01_BP`(드론, 어피어런스 `N_Drone`)에 BP 기반 호버/추적 연출 파이프라인을 붙였는데,
**정식 스폰 경로(FSBClientCharacter 프록시)에서는 캡슐(액터) 위치를 BP가 제어할 수 없음**을 실측으로 확인했다.
드론 특성상 **콜리전(캡슐)이 눈에 보이는 드론 위치를 따라가는 것이 필수 요구사항**이라 시스템 측 지원이 필요하다.

## 실측 근거 (2026-07-23, PIE)

1. **프록시 스폰 경로에서 캡슐 스톰프 확인**
   - PIE 중 `CollisionCylinder`를 임의 위치(Z=450)로 텔레포트 → 1초 내 (X=-6202, Y=-18534, **Z=122.15**)로 강제 복귀
   - 복귀 위치는 BP 연출 목표값(`CurrentVisualWorld` = X=-6195, Y=-18443, Z=120)이 **아닌 제3의 위치** = 서버 로직 위치
   - BP의 `SetActorLocation`/`SetRelativeLocation`(캡슐) 모두 매 프레임 덮어써짐. Z는 항상 122.150(지면)에 고정
   - 스폰 로그: `FSBClientCharacterCreator::TryCreateEngineProxy (AppearanceAlias=N_Drone)` → `FSBEngineWorldPartitionManager::RegisterProxy`
2. **직접 스폰(프록시 미경유) 대조 실험**
   - 동일 BP를 레벨에 직접 스폰 → 캡슐이 BP 로직대로 완전 구동 (연속 샘플: (-5956,-18491,179)→(-6173,-18327,154), Yaw 126→37, 지면핀 없음)
   - → **막는 요인은 프록시 transform 동기화 하나뿐**

## 현재 BP 구조 (참고)

- Tick → `UpdateFollowMove`(앵커 지연 갱신 + 3존 추적, `SetActorLocation(CachedAnchor)`) → `UpdatePositionPipeline`(월드 `CurrentVisualWorld` 산출) → `UpdateRotationGaze`
- 임시로 비주얼은 절대좌표 `VisualRoot`(SceneComponent) + `SBNiagara` 자식 구조로 분리해 정상 동작 중
- 단, 이 상태로는 **콜리전이 서버 위치(지면)에 남고 비주얼만 날아다님** → 요구사항 미충족

## 요청 옵션 (선호순)

1. **BP→로직 위치 푸시 API** — BlueprintCallable로 프록시/서버 로직 위치를 갱신하는 함수 (예: `SetProxyLogicLocation(FVector)`).
   드론 BP가 매 틱 연출 위치를 밀어넣으면 스캔/타게팅/월드파티션 등 위치 소비 시스템과 일관성 유지됨.
2. **특정 캐릭터 transform sync 제외 플래그** — 캐릭터 데이터/어피어런스 단위로 "engine actor transform은 클라이언트(BP) 소유" 옵션.
   드론이 연출 전용(서버 판정 위치 불필요)이라면 이쪽이 가장 단순.
3. **서버 측 호버/추적 이동** — 서버 로직이 드론 캡슐을 플레이어 추적+호버로 움직이고 BP는 미세 연출만.
   BP 연출 파라미터(3존 반경, 바빙)를 서버로 이관해야 해서 반복 수정 비용이 큼.

## 에셋/재현 정보

- BP: `/Game/Art/Character/NPC/NPC_100/Body/NPC_100_Body_01/Blueprint/NPC_100_Body_01_BP` (SBCharacter 파생)
- 테스트 맵: `/Game/Art/TA/TestLevel/LV_SBDefaultLV_WP`
- `CharMoveComp.MovementMode = MOVE_None` (CMC는 개입 없음 — 스톰퍼는 CMC가 아니라 프록시 동기화)
- 프로토타입 원본: `/Game/Art/Character/NPC/CH_NPC_Drone/BluePrints/CH_Drone_BP` (직접 스폰 전제 설계)
