# PC_01 메모리 sub-index

메인 MEMORY.md 의 200줄 한도 회피용 분리. PC_01 ABP / IK / 리그 / 헤어 작업 메모리를 여기서 관리.

## ⭐ 현재 최종 상태

- [PC_01 2026-05-18 v2 세션 종료](project_pc01_session_end_2026_05_18_v2.md) — ✅ **현재 최종**. IsLockOnTransition 변수 = IsStrafe wrapper 완성. smooth chain 양쪽 분기 시도 후 사용자 직접 제거 (효과 미미). 새 호소: 회피→Start 노이즈, Chooser row 영역. 다음 세션: PIE ANIM_REC seq 키 분석부터.
- [PC_01 2026-05-18 v1 세션 종료](project_pc01_session_end_2026_05_18.md) — 오전 세션. IsTransition() pure function 시도 후 SM rule wire 부작용으로 사용자 수동 복원.
- [PC_01 2026-05-15 세션 종료](project_pc01_session_end_2026_05_15.md) — 이전 세션.

## 구조 · 파이프라인 (참조)

- [PC_01 Chooser 평가 시점 구조](project_pc01_chooser_evaluation.md) — State 진입 시 1회 평가. 런타임 조건 변화 즉시 반영은 BlendStack 덮어쓰기로 파괴적. MM DB bias 권장.
- [PC_01_ABP AnimGraph 체인 전체 구조](project_pc01_abp_chain.md) — T3D 파싱 실측. DeadBlending=SM뒤, Inertialization=Overlay뒤. Overlay엔 Start 단계 없음 → 가드 몽타주는 Slot 재생.
- [PC_01 애니메이션 리그 디버깅 진행 상황](project_pc01_anim_debugging.md) — ABP+AnimLayer_IK+FootClamp 구조 분석 완료. 슬로프/계단 튜닝 중.
- [PC_01 MM 파이프라인 와이어링 + PSD 7개 카탈로그](project_pc01_mm_pipeline.md) — 2026-05-15 실측 정정: Chooser→BlendStack (MM은 row의 UseMotionMatching 토글로만). Stop/Pivot orphan 거짓 가설 폐기. 진짜 갭: PSS_SM_LocoLoops cardinality=1, Collector bGenerateTrajectory=False.
- [PC_01 "Pivot" = *_Turn_*_{090,180} 시리즈](reference_pc01_pivot_terminology.md) — 명명 _Pivot_ 아닌 Turn 시리즈. PSD_GroundMovingTransit에 32개 정상 등록 (2026-05-15 정정).
- [PC_01_ABP IsStarting "B 트리거 + A latch + Tag release" 설계](reference_pc01_isstarting_design.md) — A=bPrevIsStart 단독 latch, B=진입 한 틱, 외부 NOT(Pivot Tag)로 release. 한 틱 cut 회피 패턴.
- [PC_01 회피 파이프라인 종합 설계](reference_pc01_evade_pipeline_design.md) — HasEvade 트리거 확장 + MovementState 게이트 + PendingWalkMode lock. EvadeDurationThreshold=0.3.

## Foot Placement · Pelvis · Rig

- [PC_01_CtrlRig_FootClamp 구조 + 수정](project_pc01_footclamp_rig.md) — Clamp 축 매핑 스왑(Pitch↔Roll) + 값 전체 개방으로 발목 꺾임 해결.
- [PC_01 PelvisSettings 3 프로필](project_pc01_pelvis_profiles.md) — Default/Move/Prone 3개 FFootPlacementPelvisSettings struct 변수. 슬로프 인지형 + 측면 rebalance 강화.
- [Guard Overlay + IK 충돌 수정](project_guard_overlay_fix.md) — IK를 Overlay 앞으로 + layering_legs/pelvis=0.
- [Move.MaxOffset은 계단 오르막용으로 10 유지](feedback_pelvis_move_maxoffset_stairs.md) — 올리면 오르막에서 pelvis가 낮은 쪽 발 plant plane 맞추려 바닥으로 drop.
- [PlantSettings.LockType=PivotAroundAnkle은 PC_01에서 발목 고정 유발](feedback_plant_settings_locktype_ankle_pitfall.md) — 다리 밀림 호소의 직접 원인. PivotAroundBall 권장.
- [PC_01 FootClamp 전투 분기 작업 진행](project_pc01_footclamp_stance_split.md) — 옵션 A(노드 Alpha OFF) 폴백. AnimStance==BATTLE AND MovementState==IDLE 게이트. 미완 — wire 작업 + PIE 검증 남음.

## Transition · 회전 보정 (smooth chain 영역)

- [PC_01 UpdateTargetRotation trd wraparound 평활화 (2026-05-15)](project_pc01_trd_wraparound_smoothing.md) — 180° 경계 부호 반전 + 큰 step jump 평활화. PrevTargetRotationDelta 변수 + 8노드 chain. Strafe 분기.
- [trd 평활화 Alpha = Adaptive (작은=1.0 / 큰=0.075)](feedback_pc01_trd_smoothing_alpha_0_075.md) — InRange ±45° 분기.
- [PC_01 trd smoothing 적용 범위를 Transition 재생 시점으로 제한 (2026-05-15)](project_pc01_smoothing_scope_restriction.md) — Turn 매칭 X 호소 처방. bIsPlayingTransitionBack 게이트 부활.
- [PC_01 wraparound smoothing 폐기, 5/13 패턴 부활 (2026-05-15)](project_pc01_smoothing_to_zero_revert.md) — smooth chain dead code (Adaptive Alpha=1.0 구간 대부분). CF_20.B = 0.
- [PC_01 CurrentSequenceName stale 처방 (2026-05-15)](project_pc01_currentseqname_eventgraph_fix.md) — EventGraph 에 BlueprintUpdateAnimation event 신규 추가 + game thread 매 틱 Set.
- [PC_01 bIsPlayingTransitionBack 5패턴 확장 (2026-05-15)](project_pc01_gate_pattern_extended_pivot_box.md) — Contains 패턴 3 → 5 (Pivot/Box 추가). ✅ MM Continuing 메커니즘 한계 우회 패턴.
- [PC_01 PSD_GroundMovingTransit ContinuingPoseCostBias (2026-05-15)](project_pc01_psd_gmt_continuing_bias.md) — -0.01 → -1.0 (100× 강화). ✅ 검증 완료. set_cdo_property 후 save_asset P4 잠금 학습.

## Lock-on · Pivot · Sprint

- [PC_01 CircleStrafeHysteresis 메커니즘 + 갱신 한계](project_pc01_circle_strafe_hysteresis.md) — 5/25 임계, OnUpdate_GroundMoving 부재로 Hysteresis 변화 자동 반영 안 됨.
- [PC_01 락온 측면 정지 턴모션 작업 진행](project_pc01_lockon_strafe_stop_turn.md) — 태그 수정으로 1차 해결. 잔존 root motion 미적용 진단 중.
- [PC_01 Pivot Cooldown 시스템](project_pc01_pivot_cooldown.md) — IsPivoting 양 분기에 (Remain<=0) AND 게이트. Duration=0.5. 좌→우 반복 시 Pivot 도배 차단. Monolith ID 충돌 사례 첫 기록.
- [PC_01 Sprint 종료 transition 검출 Phase 1 (2026-05-14)](project_pc01_sprint_end_transition.md) — Sprint_Turn 오매칭 차단. 4변수 + UpdateVariables 검출 + ANIM_REC sset. Phase 2 (Chooser 처방) 대기.

## HasEvade · 변수 시스템

- [PC_01 HasEvade 파이프라인 + 작업 진행](project_pc01_hasevade_pipeline.md) — UpdateVariables의 bool 변수, RuleMoveFlag 트리거.
- [PC_01 회피 파이프라인 ABP 적용 완료 (2026-05-15)](project_pc01_evade_pipeline_applied.md) — EvadeDurationThreshold 0.05→0.3 + UMSB OR 게이트에 HasEvade. compile/validate/save clean.
- [PC_01_ABP AnimStance Buffer 함수 작업](project_pc01_animstance_buffer.md) — UpdateAnimStanceWithBuffer 생성 완료 (변수 4 + 26노드). UpdateStates 재배선만 ThreadSafe 메타 수동 체크 후 마무리.
- [PC_01 Velocity Smoothing Phase 1A](project_pc01_velocity_smoothing.md) — SmoothedVelocity + VelocityInterpSpeed(8.0). ANIM_REC svl 수동 마무리 필요.
- [PC_01_ABP 변수 카테고리 일괄 지정 (2026-05-15)](project_pc01_abp_variable_categories.md) — 28개 → Trajectory/Buffer/StateMachine/Travel/Evade/Foot Placement/Essential Values/AnimRewind/Combat. batch_execute 28/28.

## AnimRewindRecorder (디버거)

- [PC_01_ABP AnimRewindRecorder — 매 틱 20필드 [ANIM_REC] 로그 레코더](project_pc01_anim_rewind_recorder.md) — BP-only 디버거. PostEvaluateAnimation 끝에 20필드 캡처. **2026-05-15 분할**: 단일 FT_1(65 wire) → 카테고리당 FT (FT_2~FT_11) 10개 chain, 99 노드.
- [PC_01_ABP ANIM_REC unmapped 13필드 추가 (2026-05-18)](project_pc01_anim_rec_unmapped_added.md) — fpa/ow_a/ps_db + 10 batch (ptrd/tta/hed/sv/ise/setr/seta/pas/pms2/ppwm). Concat_StrStr 패턴 (FormatText pin auto-gen 한계 우회). compile+save 성공. PIE 검증 대기.

## PC_01 헤어 (Groom)

- [PC_01 헤어 최종 튜닝 상태 (Sanjuk)](project_pc01_hair_gravity_bug.md) — Sanjuk 5그룹 튜닝 완료. 잔존 이슈: Grp 4 Gravity=-1 + Binding이 Original 참조 중.
- [UE 5.7 Groom Physics 파라미터 레퍼런스](reference_groom_physics_params.md) — CosseratRods 솔버 모든 파라미터. 헤어 튜닝 단일 진실원.
- [Groom ProjectCollision=True는 Physics Asset 검증 전제](feedback_project_collision_requires_physassets_review.md) — PC_01에서 True 시 뒷머리 뜸.

## 폐기·롤백 이력 (참조용)

- [PC_01 SustainedDirection 결함 2건 수정 — 폐기됨](project_pc01_sustained_direction_fix.md)
- [PC_01 Sprint→Battle B_Lfoot 회전 보정 게이트 — STALE](project_pc01_sprint_to_battle_transition_fix.md)
- [PC_01 Transition 회전 보정 차단 게이트 — ROLLED BACK](project_pc01_transition_gate_phase1.md)
- [PC_01 PoseSearchData_Moving YawRate — ROLLED BACK](project_pc01_movesidedir_yaw_rate.md)
- [PoseSearchData_Moving.MaxControllerYawRate=0 은 의도, 손대지 말 것](feedback_pose_search_data_moving_default_0.md)
- [PC_01 Transition 회전 보정 게이트 최종 — OUTDATED](project_pc01_transition_gate_final.md)
- [PC_01 Transition 회전 처방 사용자 정정 — OUTDATED](project_pc01_transition_gate_user_corrected.md)
- [Mesh 시각 동작이 진짜 검증 기준](feedback_visual_mesh_over_anim_rec.md) — ANIM_REC 수치만 보고 처방 성공 판단 금지. 5/15 학습.
- [PC_01 SustainedDirection Pivot 트리거 — ARCHIVED 2026-05-13](project_pc01_sustained_direction.md)
