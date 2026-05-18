# 사용자 / 피드백 / 작업 원칙
- [사용자 역할 — SB2 애니메이션 TA](user_role.md) — SHIFTUP SB2의 UE5 애니 리깅/IK 튜닝 담당. 한국어 기본, 실행 가능한 파라미터 권장값 선호.
- [UE 기능/옵션은 한글 UI명 기본](feedback_ue_korean_ui.md) — 한글 먼저, 영문 괄호 병기. SB2 한글화 빌드 기준.
- [UE 단정 전 공식 샘플/문서 확인](feedback_verify_before_assert.md) — "GASP는 둘 다 쓰는데?" 피드백 이후 적용.
- [Gemini Code와 교차 검증 워크플로우](feedback_gemini_cross_validation.md) — 작업 시 Gemini 결과 참고+교차 검증, push는 별도 저장.

# SB2 프로젝트 · 엔진 · 환경
- [SB2 엔진은 커스텀 빌드, Monolith 직접 설치 불가](project_sb2_engine.md) — licensee-modified UE 5.7.4. Engine/Source 없음. 팀 공식 도입만이 경로.
- [SB2 Monolith 엔진팀 공식 설치 대기](project_sb2_monolith_pending.md) — 2026-04-15 엔진팀이 통합 완료 통보.
- [Monolith 인덱싱 — 최초 1회 비용 후 안전](feedback_monolith_indexing.md) — 풀 인덱스는 DDC 연쇄로 메모리 부하, 인크리멘털 3초.
- [Monolith editor 로그 캡처는 error/warning 만](feedback_monolith_log_capture_limit.md) — LogBlueprintUserMessages 미캡처. ANIM_REC는 파일 tail 폴백.
- [UE 로그 PIE 세션 + 표준 prefix `[PIE=N frame=X t=T.TTTs]`](reference_log_pie_std_prefix.md) — Phase 1 (2026-05-18). log_filter --format std / context_injector 자동 적용. 58 PIE 감지.
- [Phase 6 NOTIFY_TRACE — UE verbose 활성화 + log_filter --notify](reference_notify_trace.md) — ABP 미수정. LogAnimNotify/LogAnimMontage verbose 필요. context_injector 가이드 자동 출력.
- [animation_query 4종으로 ABP SM 전수 dump](reference_animation_query_sm_dump.md) — scripts/analyze_pc01_state_machines.py 단일 진입점. T3D 우회로 archive 가능.
- [AnimGraph 노드 편집 실측 + IsTransition gate 패턴](reference_animgraph_node_editing.md) — SM 신규 생성 불가. IsTransition은 BlendListByBool 분기 권장.
- [runreal editor_run_python 으로 Monolith 한계 우회](reference_runreal_python_bypass.md) — Chooser/SM/Enum protected 우회. PoC: scripts/runreal_chooser_inspect.py.
- [SB2 사내 MCP 3종 (미등록)](reference_sb2_internal_mcps.md) — SB2AssetParser + CodeIndexClient + BlueprintIndexer. Confluence MCP 폴더(1237549058)에서 발견.
- [SB2 사내 MCP 등록 — P4 sync + 서버 가동 대기](project_sb2_internal_mcp_pending.md) — Program/Tools/MCP/ P4 sync 누락 + 사내 서버 8000/8300 미응답.
- [SB2 PythonScriptPlugin 비활성화 — runreal/scripting 차단](feedback_sb2_python_plugin_disabled.md) — monolith.scripting.execute_script(python) 거부. SB2.uproject 에 미등록.
- [SB2 Engine source DB 비활성 — source.* 11 액션 차단](feedback_sb2_source_db_unavailable.md) — Engine/Source 없는 licensee 빌드. trigger_project_reindex 도 효과 없음. cache/ue57 + 사내 CodeIndexClient MCP 가 대체.
- [GCP VM 리모트 환경 주의사항](project_gcp_vm_setup.md) — e2-small 2GB RAM 빡빡. `.claude` 소유권 버그 시 chown으로 복구.

# SB2 시스템 구조
- [SB2 PC_01은 Motion Matching 기반](project_sb2_motion_matching.md) — BlendSpace 아닌 Pose Search DB + Chooser.
- [SB2 OverlaySystem 실제 구조](project_sb2_overlay_system.md) — ChooserTable + PDA_OverlayData + Additive Pose 패턴. Guard는 포즈 2장.
- [SB2 Show 시스템 (Art/Show/)](project_sb2_show_system.md) — 액션/스킬 연출 커스텀. AnimSequence+FX+Sound+SkillStep을 타임라인으로 묶음.
- [SB2 Mutable Crowd 시스템](project_sb2_mutable_crowd.md) — Mass AI + AnimNext(18에셋) + Mutable CO + ABP 4중 병렬.

# PC_01 (상세는 sub-index)
- [📁 PC_01 메모리 sub-index](MEMORY_PC01.md) — ABP / IK / 리그 / Transition / Lock-on / HasEvade / AnimRewindRecorder / 헤어 / 폐기 이력 정리. **현재 최종: [[pc01-session-end-2026-05-18-v2]] — IsLockOnTransition = IsStrafe wrapper 완성. smooth chain 시도→폐기. 새 호소: 회피→Start 노이즈 (Chooser row 영역). 다음: PIE ANIM_REC seq 키 분석.**

# UE 5.7 기술 레퍼런스 (소스 · API)
- [UE 5.7 FootPlacement 공식 소스 기반 ground truth](reference_foot_placement_source_5_7.md) — FootPlacement 조언의 단일 진실원.
- [GASP Foot Placement 내부 구조](reference_foot_placement_gasp.md) — Zhihu 글 기반 4단계 파이프라인.
- [UE 5.7 핵심 소스 헤더 로컬 캐시](reference_ue57_source_cache.md) — cache/ue57/ 13 헤더 + cache/ue57_contexts/ 13 가이드 (UnrealClaude 미러).
- [UE 5.7 Quaternion↔Euler 축 매핑](reference_ue57_euler_conventions.md) — EulerFromQuat(ZYX). bUseUEHandyness=true 기본.
- [KawaiiPhysics 플러그인 캐시 + 개요](reference_kawaii_physics.md) — cache/kawaii_physics/ 18 소스. UE 5.3~5.6 공식.
- [ABP 노드 bDrawDebug로 플레이 중 시각 디버그](reference_abp_bdrawdebug.md) — FootPlacement/LegIK/ControlRig 등 Details 패널.
- [Monolith HTTP JSON-RPC API 직접 호출](reference_monolith_http_api.md) — MCP 미노출 세션에서 curl로 호출.
- [Monolith ABP/AnimGraph 편집 한계](reference_monolith_animgraph_editing_limits.md) — node_type prefix, Chooser protected, SM sub-graph 미접근, P4 save 실패.
- [Sanjuk-Unreal 전용 서브 에이전트 4종](reference_sanjuk_agents.md) — AnimBP/Sim × Inspector/Tuner 매트릭스. .claude/agents/ 정의. 명시 슬래시 /inspect-abp /tune-abp /inspect-sim /tune-sim 으로 호출.
- [ABP 백업/롤백 시스템 — abp_backup.py + MonolithClient](reference_abp_backup_system.md) — Tuner 변경 직전 5종 dump 자동 백업. 변수 default 안전 복원, 그래프 토폴로지는 사용자 수동. /tune-abp 사전 조건 강제.
- [시각 검증 자동화 — screenshot.py + HighResShot](reference_visual_verification.md) — editor.run_console_command("HighResShot WxH") → Saved/Screenshots 자동 감지 → AI multimodal Read. [[feedback-visual-mesh-over-anim-rec]] 원칙 자동화. PIE 또는 viewport 모두 가능.
- [PostToolUse hook 자동 백업 + 카탈로그 갱신](reference_auto_backup_hook.md) — Monolith mutate 감지 시 백그라운드 abp_backup 자동 실행. AI 가 잊어도 hook 이 강제. discover 응답 시 카탈로그 자동 갱신. 권한 prompt 없음 (py * 이미 등록).
- [GASP 프로젝트 로컬 경로](reference_gasp_local.md) — C:\Users\SHIFTUP\Documents\Unreal Projects\GameAnimationSample\
- [GASP BP_NotifyState_EarlyTransition 패턴](reference_gasp_early_transition.md) — Transition 중 ReTransition/ToLoop 윈도우.
