# KawaiiPhysics 종합 리서치 + SB2 적용 분석

작성: 2026-06-12 · 출처: GitHub(pafuhana1213) + 로컬 소스 캐시 + SB2 Monolith 실측 + Confluence 인수인계 문서("군중", pageId 1611825177)

---

## 1. 플러그인 개요

| 항목 | 내용 |
|------|------|
| 리포 | https://github.com/pafuhana1213/KawaiiPhysics |
| 최신 버전 | **v1.20.0** (2026-01, UE 5.7 공식 지원 추가) — [Discussion #185](https://github.com/pafuhana1213/KawaiiPhysics/discussions/185) |
| 지원 엔진 | UE 5.3~5.7 (v1.20.0 기준), UE 4.27은 v1.11.1 레거시 |
| 라이선스 | MIT (상업 사용 가능). Fab / GitHub / Booth 배포 |
| 방식 | Verlet 적분 기반 pseudo-physics. PhysX/Chaos 의존 없음. AnimGraph 노드 1개로 셋업 |
| 모듈 | `KawaiiPhysics`(Runtime, PostConfigInit) + `KawaiiPhysicsEd`(UncookedOnly) |

머리카락·치마·가슴·액세서리 등 **얇은 세컨더리 본 체인** 전용. 망토/드레스급 무거운 천은 Chaos Cloth 영역.

## 2. 핵심 파라미터 (`FKawaiiPhysicsSettings`)

플러그인 기본값 — 출처: `cache/kawaii_physics/AnimNode_KawaiiPhysics.h`

| 파라미터 | 기본값 | 의미 |
|---------|-------|------|
| Damping | 0.1 | 감쇠. 작을수록 가속도가 더 반영(출렁임 큼) |
| Stiffness | 0.05 | 강성. 클수록 원래 포즈 유지 |
| WorldDampingLocation | 0.8 | 컴포넌트 **이동**의 물리 반영도 |
| WorldDampingRotation | 0.8 | 컴포넌트 **회전**의 물리 반영도 |
| Radius | 3.0 | 본별 충돌 반경 |
| LimitAngle | 0.0 | 회전 제한 각(0=무제한) |

노드 레벨 주요 항목:

- **본 선택**: RootBone + ExcludeBones + DummyBoneLength(말단 더미 본) + BoneForwardAxis
- **시뮬 공간**: ComponentSpace(기본) / WorldSpace / BaseBoneSpace
- **안정화**: TargetFramerate(60) / WarmUpFrames / TeleportDistanceThreshold(300) / TeleportRotationThreshold(10°)
- **커브 보정**: Damping/Stiffness/WorldDamping/Radius/LimitAngle 각각 본 체인 길이 비율(0~1) 기반 커브 승산 가능
- **충돌**: Spherical/Capsule/Box/Planar Limit — 노드 직접, `LimitsDataAsset`(재사용), `PhysicsAssetForLimits` 3가지 소스. WorldCollision 옵션(고비용)
- **외력**: InstancedStruct 배열 — Basic(방향), Curve(시간 커브), Gravity(캐릭터 중력 연동), Wind(WindDirectionalSource) + AnimNotify 2종으로 구간 적용
- **본 제약**: XPBD 거리 제약(BoneConstraints, ComplianceType 7종) — 치마 본 사이 벌어짐 방지
- **SyncBone**: 다리 본 움직임을 치마 본에 전달해 관통 방지 (거리 감쇠 지원)
- **공유 충돌**: GameplayTag 그룹으로 캐릭터 간 충돌 동기화 (WorldSubsystem, 더블버퍼)
- **BP API**: `KawaiiPhysicsLibrary` — 전 파라미터 런타임 Get/Set, ResetDynamics, 외력 추가/제거, Alpha 제어

상세 전체 파라미터 레퍼런스는 로컬 캐시 헤더 참조:
`C:\Users\SHIFTUP\.claude\projects\C--Dev-Sanjuk-Unreal\cache\kawaii_physics\`

## 3. SB2 설치 상태 — ✅ 실측 2026-06-12

| 항목 | 값 |
|------|-----|
| 설치 위치 | `E:\Perforce\SB2\Workspace\Internal\SB2\Plugins\KawaiiPhysics\` — **바이너리 전용** (Binaries + .uplugin, Source 미포함. DLL 빌드 2026-06-10) |
| **설치 버전** | **v1.19.0** (`KawaiiPhysics.uplugin` VersionName) |
| 엔진 | SB2 custom UE 5.7.4 — UE 5.7 공식 지원은 v1.20.0부터이나, 엔진팀 빌드 바이너리로 정상 동작 중 |
| 1.19.0 기능 (DLL 문자열 실측) | ✅ AdditionalRootBones / ExternalForces / BoneConstraints / WarmUpFrames / LimitsDataAsset / PhysicsAssetForLimits / DummyBoneLength · ❌ SyncBone / 공유충돌(v1.20 신기능) |

⚠ 업그레이드 검토 시: v1.20.0은 UE 5.7 정식 대응 + 샘플 크래시 수정. 단 P4 관리 에셋과 노드 직렬화 호환은 별도 확인 필요.

## 4. SB2 사용처 전수 맵 — ✅ Monolith 실측 2026-06-12 (project search "Kawaii", 300 히트 dedupe)

전부 **AnimBlueprint**(대부분 PostProcess ABP). 카테고리별:

| 카테고리 | 에셋 | 용도(루트 본 기준) |
|---------|------|------|
| **PC** | `PC_01_Body_001_PostProcess` | breast 10본 그룹 + thigh_bck 2본 |
| **PC** | `Evie_Body_ABP` | (14 히트 — 미상세 조사) |
| **NPC** | `NPC_001_Body_01_PostProcess` | 액세서리 19노드: pelvis_acc / clavicle_acc / collar A·B·C / hood / lowerarm_acc / calf_acc |
| **몬스터** | M_001~M_010 `*_Body_01_PostProcess` (M_009는 TypeC), `M_004_Hair_01_PostProcess`, `M_001_Weapon_PostProcess` | 바디 부속물·헤어·무기 |
| **군중(Mutable)** | Crowd_02/03/04 헤어 AnimBP 6종(`Crowd_04_Hair_01_AnimBp` 등) + Crowd_04 Lower(치마) PostProcess 9종 | 헤어 4루트 / 치마 7~8루트 |
| **아이템** | `Item_Outer_01_ABP`, `Item_Outer_01_PostProcess` | 외투 |

총 **32개 ABP**에서 사용. PC_01 메인 헤어는 KawaiiPhysics가 아닌 SBStableRodsSystem(커스텀 Dataflow) — 분리 운용.

## 5. SB2 공통 적용 패턴 — ✅ 실측

```
입력 포즈(InPose) → ControlRig → [LocalToComponentSpace]
  → KawaiiPhysics 노드 직렬 체인 (루트 본 1개당 노드 1개)
  → [ComponentToLocalSpace] → 출력 포즈
```

- **PostProcess ABP** 방식: 메인 ABP/MM 로직과 분리, 메시 에셋의 PostProcess AnimBP 슬롯에 연결
- **설정 공유**: `Make KawaiiPhysicsSettings` 스트럭트 노드 1개의 출력을 같은 부위 노드 여러 개의 PhysicsSettings 핀에 분배 (PC_01: 3세트/12노드, 군중 치마: 1세트/8노드)
- **중력 배선**: `MakeVector(0,0,-2000)` 1개 → 전 노드 Gravity 핀 (군중 치마 실측). NPC_001도 Gravity 핀 연결형
- **노드 기본 Alpha=1.0**, 커브/노티파이 기반 알파 제어 미사용 (실측 범위 내)
- PC_01 PostProcess에는 KawaiiPhysics 외에 UE 내장 **SpringBone**(thigh_bck_01, hip_01, breast)과 **PoseDriver** 다수 병행 — 레거시 혼재 상태

## 6. 실측 파라미터 값 비교

| 에셋 / 그룹 | Damping | Stiffness | WDL | WDR | Radius | LimitAngle |
|------------|--------:|----------:|----:|----:|-------:|-----------:|
| 플러그인 기본값 | 0.10 | 0.05 | 0.8 | 0.8 | 3.0 | 0 |
| PC_01 breast 8본(up/dn/in/out) | 0.50 | 0.10 | 1.0 | 1.0 | 2.0 | 5 |
| PC_01 breast_l/r 메인 | 0.80 | 0.15 | 1.0 | 1.0 | 3.0 | 3 |
| PC_01 thigh_bck | 1.00 | 0.12 | 1.0 | 1.0 | 2.0 | 5 |
| 군중 헤어 A그룹 (hair_A_out) | 0.35 | 0.05 | 1.0 | 1.0 | 0.5 | 45 |
| 군중 헤어 B그룹 (hair_B_out) | 0.35 | 0.05 | 1.0 | 1.0 | 1.0 | 45 |
| 군중 치마 (skirt 8루트 공통) | 0.40 | 0.05 | **2.0** | **2.0** | 2.0 | 30 |

경향: PC 가슴/허벅지는 고감쇠+저각도제한(미세 출렁임), 군중 헤어/치마는 저감쇠+큰 LimitAngle(존재감 있는 출렁임을 각도로만 제한). WorldDamping 2.0(치마)은 1.0 초과 — 이동 반영 과장값.

## 7. Confluence 인수인계 문서 내용 ("군중")

https://shiftupcorp.atlassian.net/wiki/spaces/~712020fe37626a375148458345b2dab4dbde10/pages/1611825177

- **기본 바디**: `Crowd_Body_PostProcess` ABP 사용 — 내부는 `Crowd_Body_Base_CtrlRig` 호출만 (KawaiiPhysics 없음, 실측 일치)
- **치마 리소스**: 별도 PostProcess ABP — `Crowd_Body_Base_CtrlRig` + `Crowd_04_Skirt_CtrlRig` 체인 뒤 KawaiiPhysics 체인
- **헤어**: 파츠별 전용 AnimBP (`Crowd_04_Hair_06_AnimBP` 등) + **UAF AnimGraph 에셋 병행** (Mass 군중은 AnimNext 경로 — [[project-sb2-mutable-crowd]] 와 일치)
- **본 네이밍 컨벤션** (DCC 스크린샷 기준):
  - 치마: `skirt_{A|B|C}_out_##_{fr|bk|l|r}` — A=앞/뒤 메인, B=측면, C=측후방 (색상 코딩: 앞=주황, 뒤=핑크, 측=노랑, C=시안)
  - 헤어: `hair_{A|B}_out_##_{bk|l|r}` — A_bk=뒷머리 중앙, A/B 측면 그룹
- **Mutable 연계**: Customizable Object 파츠(Lower/Hair 베리에이션)마다 개별 PostProcess ABP/AnimBP를 붙이는 구조 (개요 이미지)

## 8. 운용 시 주의점

1. **버전 갭**: 설치 1.19.0 vs 최신 1.20.0(UE5.7 정식). SyncBone/공유충돌은 1.19에 없음(DLL 실측). 현재 동작에 문제 없으면 유지가 안전
2. **Crowd 본체 vs 파츠**: 본체 PostProcess에는 물리 없음 — 치마/헤어 파츠 ABP에만 있음. 군중 물리 이슈는 파츠 ABP부터 볼 것
3. **PC_01 혼재**: SpringBone(레거시)과 KawaiiPhysics가 같은 부위 계열(breast, thigh/hip)에 공존 — 튜닝 시 양쪽 모두 확인 필요
4. **충돌 부분 사용** (✅ 6/12 정정): PC_01은 Evie 폴더의 `arm_collision`(LimitsDataAsset) + `KawaiiPhysics_Curve_Dn01`(CurveFloat) 참조 확인. 군중/NPC/몬스터는 Limits 배선 미확인 — 치마 관통 방지는 CtrlRig leg-follow + LimitAngle 의존
5. **runtime 제어**: `KawaiiPhysicsLibrary`로 런타임 파라미터 변경 가능하나 SB2 그래프는 모두 정적 Make 스트럭트 — 동적 제어 미사용

## 8.5 개선 제안 (✅ 실측 기반 2026-06-12 — 상세는 Confluence "KawaiiPhysics" 페이지 §10/§11)

**KawaiiPhysics**: ① PC_01의 Evie 크로스 참조 정리(높음) ② 군중 다수 인스턴스 비용 — bUpdatePhysicsSettingsInGame=false + AdditionalRootBones 노드 통합 8→1~2(높음) ③ 군중 충돌 미배선 — CapsuleLimit 공유 배선, 근본 해결 SyncBone은 v1.20 필요 ④ SpringBone 혼재 통일 ⑤ 치마 WorldDamping 2.0 의도 확인 ⑥ 프리셋 표준화 ⑦ ResetDynamics/WarmUp 운용 ⑧ 중력 -2000 표준화 ⑨ v1.20 업그레이드(엔진팀 빌드 필요)

**ControlRig (Crowd_04_Skirt_CtrlRig 그래프 실측 — 203노드/262링크, 컨트롤 0, ForLoop/Array 0)**: 로직 = thigh 내적→Remap→TransformLerp→SetTransform의 leg-follow. ① 본별 복붙 8회 → For Each+Array 재구조화(~1/8) ② 본 이름 하드코딩 11개 → 네이밍 패턴 동적 수집으로 파츠 9종 공용 릭 1개화 ③ Base+Skirt 직렬 VM 2회 → 통합 또는 LOD Threshold ④ 회전만 반영(translation 미반영 → 관통 잔존 가능) ⑤ PC_01 측 Post/BtoB 릭 미분석(후속)

## 9. 참고 링크

- 공식 위키: https://github.com/pafuhana1213/KawaiiPhysics/wiki/Home-en
- v1.20.0 릴리스 노트: https://github.com/pafuhana1213/KawaiiPhysics/discussions/185
- FAQ: https://github.com/pafuhana1213/KawaiiPhysics/wiki/FAQ-en
- DeepWiki(AI 생성 구조 분석): https://deepwiki.com/pafuhana1213/KawaiiPhysics
- 로컬 소스 캐시: `~/.claude/projects/C--Dev-Sanjuk-Unreal/cache/kawaii_physics/` (18파일)
