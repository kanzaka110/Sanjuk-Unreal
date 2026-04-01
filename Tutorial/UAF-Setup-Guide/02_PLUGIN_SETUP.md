# 02. 플러그인 설정

[<- 이전: UAF 개요](./01_UAF_OVERVIEW.md) | [목차](./00_INDEX.md) | [다음: 핵심 에셋 이해 ->](./03_CORE_ASSETS.md)

---

## 2.1 필수 플러그인

Edit -> Plugins -> "UAF" 검색

| 플러그인 | 필수 여부 | 설명 |
|---------|----------|------|
| **Unreal Animation Framework** | **필수** | UAF 핵심 프레임워크 |
| **UAF Anim Graph** | **필수** | 애니메이션 그래프 시스템 |

> **경고**: "Unreal Animation Framework"만 활성화하고 "UAF Anim Graph"를 빠뜨리면 에디터가 **크래시**합니다! 반드시 둘 다 활성화하세요.
>
> 원인: UAF가 `/Script/AnimNextAnimGraph.RigUnit_AnimNextTraitStack`을 로드하려 하는데 UAF Anim Graph 플러그인 없이는 찾을 수 없습니다.

---

## 2.2 기능별 선택 플러그인

### Motion Matching 사용 시

| 플러그인 | 설명 |
|---------|------|
| **Pose Search** | Motion Matching 핵심 |
| **UAF Pose Search** | UAF와 PoseSearch 연동 |
| **Chooser** | Chooser Table (DB 선택) |
| **UAF Chooser** | UAF와 Chooser 연동 |

### Mover 2.0 사용 시

| 플러그인 | 설명 |
|---------|------|
| **Mover** | 차세대 캐릭터 무브먼트 |
| **Mover UAF** | Mover와 UAF 연동 |

### 기타 통합 플러그인

| 플러그인 | 설명 |
|---------|------|
| **UAF Control Rig** | Control Rig 연동 (Foot Placement 등) |
| **UAF State Tree** | StateTree 연동 |
| **UAF Warping** | 애니메이션 워핑 |
| **UAF Mirroring** | 실시간 미러링 |
| **RigLogic for UAF** | MetaHuman RigLogic 연동 |

---

## 2.3 권장 플러그인 구성

### 최소 구성 (UAF 테스트용)
```
[v] Unreal Animation Framework
[v] UAF Anim Graph
```

### Motion Matching 구성
```
[v] Unreal Animation Framework
[v] UAF Anim Graph
[v] Pose Search
[v] UAF Pose Search
[v] Chooser
[v] UAF Chooser
```

### 풀 구성 (GASP 스타일)
```
[v] Unreal Animation Framework
[v] UAF Anim Graph
[v] Pose Search
[v] UAF Pose Search
[v] Chooser
[v] UAF Chooser
[v] Mover
[v] Mover UAF
[v] UAF Control Rig
[v] UAF Warping
[v] UAF Mirroring
[v] UAF State Tree
[v] Animation Locomotion Library
[v] Animation Warping
[v] Motion Warping
```

---

## 2.4 플러그인 활성화 후

1. **에디터 재시작** (필수!)
2. Content Browser에서 우클릭 -> **Animation** 메뉴 확인
3. 다음 항목들이 보이면 성공:
   - UAF Asset Wizard
   - UAF Animation Graph
   - UAF System
   - UAF Workspace
   - UAF Shared Variables
   - 등등

---

[<- 이전: UAF 개요](./01_UAF_OVERVIEW.md) | [목차](./00_INDEX.md) | [다음: 핵심 에셋 이해 ->](./03_CORE_ASSETS.md)
