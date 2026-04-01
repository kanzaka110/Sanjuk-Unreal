# 4. 기본 사용법

## 4.1 첫 번째 명령 - 프로젝트 탐색

연결이 되었으면, Claude Code에서 자연어로 UE 프로젝트를 탐색해봅시다.

### 프로젝트 에셋 확인

```
프로젝트에 있는 애니메이션 에셋들을 모두 보여줘
```

```
현재 프로젝트의 스켈레탈 메시 목록을 알려줘
```

```
Content 폴더에 있는 Animation Blueprint를 찾아줘
```

### 에셋 상세 정보 확인

```
/Game/Characters/Mannequins/Animations/ABP_Manny 에셋의 구조를 분석해줘
```

```
이 Animation Blueprint에 어떤 State Machine이 있는지 보여줘
```

## 4.2 간단한 에셋 생성

### AnimSequence 관련 작업

```
/Game/Animations/ 폴더에 있는 모든 AnimSequence를 나열해줘
```

```
ABP_Manny의 Idle 애니메이션에 Notify를 추가해줘.
이름은 "FootstepNotify"이고, 0.5초 지점에 배치해줘
```

### AnimMontage 생성

```
/Game/Animations/Idle_Anim을 기반으로 새 AnimMontage를 만들어줘.
이름은 "AM_Idle_Montage"로 하고, DefaultSlot에 배치해줘
```

### BlendSpace 생성

```
1D BlendSpace를 만들어줘.
이름: BS_Walk_Run
축: Speed (0 ~ 600)
샘플 포인트:
- Speed 0: Idle 애니메이션
- Speed 200: Walk 애니메이션
- Speed 600: Run 애니메이션
```

## 4.3 에셋 수정

### 기존 에셋 편집

```
AM_Idle_Montage에 새 섹션 "Section_Loop"를 추가해줘
```

```
BS_Walk_Run의 Speed 300 지점에 Jog 애니메이션 샘플을 추가해줘
```

### 노티파이 관리

```
Idle_Anim의 모든 Notify를 보여줘
```

```
Idle_Anim의 0.3초 지점에 Sound Notify를 추가해줘.
사운드 에셋은 /Game/Sounds/Footstep_01
```

## 4.4 자주 사용하는 명령 패턴

### 조회 패턴

| 자연어 명령 | 내부 동작 |
|------------|----------|
| "애니메이션 에셋 목록" | `animation_query("list_sequences", ...)` |
| "AnimBP 구조 분석" | `animation_query("inspect_abp", ...)` |
| "State Machine 정보" | `animation_query("list_states", ...)` |
| "BlendSpace 샘플 포인트" | `animation_query("get_blend_space", ...)` |

### 생성 패턴

| 자연어 명령 | 내부 동작 |
|------------|----------|
| "Montage 만들어줘" | `animation_query("create_montage", ...)` |
| "BlendSpace 생성" | `animation_query("create_blend_space", ...)` |
| "스테이트 추가" | `animation_query("add_state", ...)` |
| "Notify 추가" | `animation_query("add_notify", ...)` |

### 수정 패턴

| 자연어 명령 | 내부 동작 |
|------------|----------|
| "섹션 추가" | `animation_query("add_montage_section", ...)` |
| "트랜지션 룰 설정" | `animation_query("set_transition_rule", ...)` |
| "블렌딩 설정 변경" | `animation_query("set_blending", ...)` |

> 💡 **팁**: 내부 동작을 외울 필요 없습니다!
> 자연어로 요청하면 Claude Code + Monolith 스킬이 알아서 적절한 액션을 선택합니다.

## 4.5 결과 확인

AI가 에셋을 생성/수정한 후:

1. **UE 에디터에서 직접 확인**: Content Browser에서 해당 에셋 더블클릭
2. **AI에게 확인 요청**: "방금 만든 Montage의 구조를 다시 보여줘"
3. **변경사항 저장**: `Ctrl+S` 또는 "이 에셋을 저장해줘"

> ⚠️ AI가 만든 에셋은 UE 에디터에서 즉시 반영되지만,
> **저장하지 않으면 에디터를 닫을 때 사라집니다!**

## 체크리스트

- [ ] 프로젝트 에셋 목록 조회 성공
- [ ] 에셋 상세 정보 확인 가능
- [ ] 간단한 에셋 생성 (Montage 또는 BlendSpace) 성공
- [ ] UE 에디터에서 생성된 에셋 확인

---
[← 이전: Claude Code 연결](03-Connect-Claude-Code.md) | [다음: 애니메이션 워크플로우 →](05-Animation-Workflow.md)
