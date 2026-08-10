# Monolith 워크플로우 매크로

자주 사용하는 멀티 액션 시퀀스를 정의. 이 매크로 패턴을 따라 작업 효율을 높인다.

## 매크로 1: 캐릭터 로코모션 ABP 세팅

목표: 캐릭터에 기본 로코모션 State Machine 구축

```
1. animation_query("list_sequences") → 사용 가능한 이동 애니메이션 확인
2. animation_query("create_blend_space") → Speed 기반 1D BlendSpace 생성
3. animation_query("inspect_abp") → 대상 ABP 구조 확인
4. animation_query("add_state") × N → Idle, Walk, Jog, Sprint 상태 추가
5. animation_query("set_transition_rule") × N → Speed 임계값 기반 전환 규칙
6. animation_query("add_notify") → Footstep 노티파이 추가
```

## 매크로 2: 몽타주 전투 세팅

목표: 공격 AnimMontage 섹션 분할 + 노티파이

```
1. animation_query("list_sequences") → 공격 애니메이션 확인
2. animation_query("create_montage") → 몽타주 생성
3. animation_query("add_section") × 3 → Windup, Strike, Recovery 분할
4. animation_query("add_notify", type="AnimNotify_PlaySound") → 타격 사운드
5. animation_query("add_notify", type="AnimNotifyState") → 판정 윈도우
6. animation_query("set_slot") → DefaultSlot 또는 UpperBody 설정
```

## 매크로 3: MetaHuman 리타겟 세팅

목표: MetaHuman 스켈레톤에 기존 애니메이션 리타겟

```
1. animation_query("list_skeletons") → 소스/타겟 스켈레톤 확인
2. animation_query("inspect_skeleton") → 본 구조 비교
3. animation_query("create_ik_retargeter") → IK Retargeter 생성
4. animation_query("set_bone_chain") × N → 본 체인 매핑
5. animation_query("retarget_animation") → 배치 리타겟 실행
```

## 매크로 4: AI 행동트리 + 애니메이션 연동

목표: AI BT에서 애니메이션 재생까지 연결

```
1. MonolithAI: build_behavior_tree_from_spec() → BT 생성
2. MonolithAI: set_blackboard_key() → 애니메이션 관련 키 설정
3. animation_query("create_montage") → AI용 몽타주 생성
4. blueprint_query("add_node") → BTTask에서 PlayMontage 호출
5. MonolithAI: set_perception() → 감지 트리거 연결
```

## 매크로 5: Chaos Cloth 기본 세팅

목표: 캐릭터 의상에 Cloth 시뮬레이션 적용

```
1. animation_query("inspect_skeleton") → Physics Asset 확인
2. 에디터에서 Cloth Paint → 가중치 설정 (수동)
3. config_query("set_cloth_config") → Wind, Gravity, Damping 파라미터
4. config_query("set_collision") → 캡슐/구체 콜리전 추가
5. editor_query("simulate") → PIE에서 결과 확인
```

## 매크로 6: Groom Maya→UE 파이프라인 (cross-MCP)

목표: Maya XGen Groom 을 UE GroomAsset 으로 import + 메타 cross-check + Physics 검증.

전제: maya MCP + Monolith MCP 둘 다 응답 중.

```
1. (Maya) mcp__maya__scene_open → Groom 작업 씬 로드
2. (Maya) mcp__maya__dump_groom_metadata(verbose=True)
   → xgen_legacy[] / interactive_groom[] / alembic_attrs[] 확인
   → groom_guides / groom_root_uv / groom_group_id schema 일치 검증
3. (외부) Maya 에서 Alembic 익스포트 (.abc) — 자동화 미지원, 수동 또는 Maya 스크립트
4. (UE) Monolith editor_query("list_assets",
        directory="/Game/Art/Character/PC/<TARGET>/Hair",
        class_filter="GroomAsset") → 기존 Groom 자산 확인
5. (UE) Monolith editor_query("get_asset_info",
        asset_path="<Groom>", include_properties=True)
   → 현재 PhysicsAsset / BindingAsset / Material 슬롯 확인
6. (UE) Monolith blueprint_query("set_cdo_property", ...) 또는
        editor_query("set_asset_property", ...) 로 그룹 파라미터 조정
   → 메모리 [[reference-groom-physics-params]] 의 CosseratRods 솔버 권장값 참조
7. (UE) Monolith animation_query("get_physics_asset_info") → 콜리전 검증
   → [[feedback-project-collision-requires-physassets-review]] 의 ProjectCollision=True 시
     PhysAsset 캡슐이 메시 외부로 빠지는지 확인
8. (UE) PIE 에서 헤어 시뮬 — DrawDebug 또는 콘솔 `r.HairStrands.DebugMode 6`
```

주의:
- [[project-pc01-hair-gravity-bug]] 처럼 Grp 별 Gravity / BendStiffness 가 다른 케이스 → 6단계에서 그룹 단위 set
- Maya 에서 Binding asset 이 Original 메시 참조 중이면 UE에서 강제 re-bind 필요 (수동)

## 매크로 사용 원칙

- 각 단계 실행 후 결과 확인 (실패 시 즉시 중단 + 원인 분석)
- 에셋 경로는 Copy Reference로 정확히 취득
- 벌크 작업은 JSON spec 패턴 사용 (build_*_from_spec)
- 수동 작업이 필요한 단계는 명확히 표시하여 사용자에게 안내
