# [협의 요청] NPC_100 드론 — 스캔 스킬 Show의 AnimMontage 키가 실행되지 않음

작성: 2026-07-28, 애니메이션 TA. 대상: SB 전투/연출(Show) 프로그래밍팀.
관련 선행 문서: `drone-npc100-proxy-transform-request.md` (프록시 transform 협의, 2026-07-23)

## 요약

`N_Drone_Normal_Scan`(드론 스캔) 스킬에서 Show(연출)의 **다른 키(니아가라 등)는 실행되는데 `SBShowAnimMontageKey`만 어떤 환경에서도 실행되지 않는다.**
런타임(PIE)과 ShowMaker 프리뷰 양쪽에서 캐스터(드론) 애님 인스턴스에 몽타주가 단 한 번도 재생되지 않음을 계측으로 확인했다.
애니 에셋/스켈레톤/데이터 체인은 전부 정상임을 검증했으므로, **몽타주 키의 타겟 resolve 또는 실행 조건(SB C++ 내부)** 확인을 요청한다.

## 실측 근거 (2026-07-28, PIE + ShowMaker)

계측 방법: 에디터 틱 콜백으로 0.05~0.1초 간격 샘플링 — 대상 액터의 모든 SkeletalMeshComponent에서
`GetAnimInstance()` + linked instances의 `IsAnyMontagePlaying()` / `GetCurrentActiveMontage()` 기록.

1. **런타임: Show 스테이지는 정상 구동**
   - `SkillActiveStepTable`의 `N_Drone_Normal_Scan_Cast1.ShowPath=None`(첫 스텝 Show 공백) 상태에서는 스킬 사용마다
     `[FSBPresentationSkillAction::CheckElapsedTime] Invaild show stage handle` 발생 (12/12회 상관, 플레이어 스킬에선 미발생)
   - Cast1에 ShowPath를 임시 주입하자 위 에러 소멸(이후 20여 회 0건) + Show 산물 `SBShowNiagaraCollisionMarkerActor` 스폰 확인
     → **스테이지 생성/키 실행 프레임은 동작. 첫 스텝 Show 공백 시 전체 연출이 죽는 동작도 확인** (데이터 수정 요청 예정)
2. **런타임: 몽타주만 0회**
   - 위 조건에서 드론 메시(메인+링크드 인스턴스 전부)에 몽타주 재생 기록 없음. 스켈레톤 불일치 등 워닝 로그도 전무
3. **ShowMaker 프리뷰에서도 몽타주 0회**
   - `N_Drone_Scan_Tap` Show를 ShowMaker에서 재생(제작자 프리뷰 설정: Caster=N_Drone, CasterActor=NPC_100_Body_01_BP)
   - 프리뷰 월드(Transient World)의 드론 프리뷰 액터 애님 인스턴스를 0.05s 간격 감시 — 몽타주 재생 없음, 모션 없음
4. **애니/데이터 무결 검증**
   - Show 내부 키 실측: `N_Drone_Scan_ChargeStart`에 `SBShowAnimMontageKey` 2개(0.0s ChargeStart, 0.5s ChargeLoop), `N_Drone_Scan_Tap`에 1개 — AnimSequencePath 정상 참조
   - 스킬 애니 8종 존재, 스켈레톤 = `NPC_100_Body_01_Skeleton` (대상 메시와 일치)
   - PIE 중 동일 애니를 `PlayAnimation`(single node)으로 직접 재생 시 드론에서 모션 정상 출력
5. **ABP 변인 배제 (3종 전수)**
   - ① 원본 ABP(`NPC_100_Body_01_ABP` 뎁봇 리비전: AnimInstance 부모, `입력포즈→Slot 'FullBody'→출력` 구조) ② 순정 AnimInstance 커스텀 ③ `SBActorAnimInstance` 부모 + DefaultSlot/FullBody 슬롯 신규 ABP — **셋 모두 몽타주 0회**
   - 특히 ①은 최종 재검증: Cast1 임시 주입으로 스테이지 정상(에러 0) 조건에서 스킬 4회 → 몽타주 0회. 같은 인스턴스에 `PlaySlotAnimationAsDynamicMontage(anim, 'FullBody')` 수동 호출 시에는 **모션 육안 확인** — 슬롯/몽타주 경로는 정상
   - `bShowWithCasterDrone` True/False 차이 없음
6. **키 프로퍼티 실측**: `SBShowAnimMontageKey` = AnimSequencePath / StartTime / Duration / LoopCount / PlayRate / bDisableHeadLookAtIK 뿐 — **타겟·슬롯 선택 필드 없음** → 재생 대상/슬롯 결정은 C++ 내부 고정으로 추정

## 질문 / 요청

1. `SBShowAnimMontageKey`가 **캐스터 아바타의 애님 인스턴스를 resolve하여 몽타주를 재생하는 조건**이 무엇인가?
   (특정 컴포넌트 등록? SB 애님 시스템 등록 상태? 캐릭터 타입/어피어런스 요건? 소환수(SummonCharacterTable) 캐스터 제약?)
2. NPC_100(어피어런스 `N_Drone`, `NPC_100_Body_01_BP` — SBCharacter 파생 TA 커스텀 BP)에서 이 조건이 충족되지 않는 지점 확인 요청
3. 드론이 스킬 연출 몽타주를 받으려면 **BP/ABP 쪽에서 갖춰야 할 표준 셋업**(요구 슬롯 이름 포함)을 알려주면 TA 쪽에서 맞추겠다
4. (데이터팀 전달) `N_Drone_Normal_Scan_Cast1.ShowPath=None`이면 스킬 전체 연출이 invalid stage로 죽는 문제 — 첫 스텝에 Show 지정 또는 시스템에서 공백 허용 처리 필요

## 에셋/재현 정보

- Show: `/Game/Art/Show/NPC/NPC_100/Skill/N_Drone_Scan_Tap`, `N_Drone_Scan_ChargeStart` (SBShowData)
- 애니: `/Game/Art/Character/NPC/NPC_100/Animation/N_Drone_Scan_*` (8종)
- BP: `/Game/Art/Character/NPC/NPC_100/Body/NPC_100_Body_01/Blueprint/NPC_100_Body_01_BP`
- ABP(현재): 동 폴더 `NPC_100_Body_ABP` (SBActorAnimInstance 파생, DefaultSlot/FullBody 슬롯)
- 데이터: SkillTable/SkillActiveStepTable `N_Drone_Normal_Scan*` (FileSuffix=PC)
- 재현: PIE에서 드론 소환 상태로 스캔 스킬 사용 → 니아가라/이펙트는 나오나 드론 모션 없음. ShowMaker에서 Tap Show 재생 시에도 모션 없음
