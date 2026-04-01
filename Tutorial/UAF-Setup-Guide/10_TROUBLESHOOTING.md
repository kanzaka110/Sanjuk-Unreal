# 10. 문제 해결 & 주의사항

[<- 이전: 기술 아키텍처](./09_ARCHITECTURE.md) | [목차](./00_INDEX.md) | [다음: 참고 자료 ->](./APPENDIX_RESOURCES.md)

---

## 10.1 알려진 크래시

### 크래시 1: UAF Anim Graph 플러그인 누락

**증상**: Module/System 생성 시 에디터 크래시
**원인**: "Unreal Animation Framework"만 활성화하고 "UAF Anim Graph"를 빠뜨림
**해결**: 반드시 **두 플러그인 모두** 활성화

```
[v] Unreal Animation Framework    <- 이것만으로는 부족!
[v] UAF Anim Graph                <- 이것도 반드시 필요!
```

### 크래시 2: Workspace에서 자식 노드 더블클릭

**증상**: Workspace 뷰에서 Module의 자식 노드를 더블클릭하면 100% 크래시
**원인**: 에디터 버그 (UE 5.6~5.7)
**해결**: 더블클릭 대신 **우클릭 메뉴** 사용

### 크래시 3: 에디터 재시작 후 에셋 레지스트리 문제

**증상**: Content Browser에서 UAF 에셋이 보이지 않음
**원인**: 크래시로 에셋 레지스트리 캐시 손상
**해결**:
1. Python 콘솔에서 스캔:
   ```python
   import unreal
   reg = unreal.AssetRegistryHelpers.get_asset_registry()
   reg.scan_paths_synchronous(["/Game/Characters/UAF/"], True)
   ```
2. 안 되면 에디터 재시작

---

## 10.2 UAF가 작동하지 않는 경우

### 문제: 캐릭터가 T-포즈/A-포즈

**원인 1**: SkeletalMeshComponent 애니메이션이 비활성화되지 않음
```
SkeletalMeshComponent > Animation Mode: "No Animation"    <- 확인!
SkeletalMeshComponent > Anim Class: None                   <- 확인!
```

**원인 2**: AnimNextComponent에 System이 할당되지 않음
```
AnimNextComponent > Module: Sys_MyCharacter                <- 확인!
AnimNextComponent > Auto Activate: true                    <- 확인!
```

**원인 3**: System EventGraph가 비어있음
- Initialize에 Make Reference Pose 연결 확인
- PrePhysics에 Evaluate Graph + Write Pose 연결 확인

### 문제: 컴파일 에러 (빨간 노드)

**원인**: 참조 에셋 누락 또는 바인딩 미설정
**해결**:
1. 빨간 노드 클릭 -> 에러 메시지 확인
2. Details에서 누락된 에셋 할당
3. 바인딩 소스 설정

### 문제: Motion Matching이 작동하지 않음

**체크리스트**:
- [ ] PoseSearch 플러그인 활성화?
- [ ] UAF Pose Search 플러그인 활성화?
- [ ] PoseSearchDatabase에 시퀀스가 포함됨?
- [ ] Calculate Trajectory 노드가 Evaluate 전에 연결됨?
- [ ] Chooser Table이 올바른 DB를 반환하는지?

---

## 10.3 성능 고려사항

### UAF의 성능 이점
- AnimGameThreadTime을 소비하지 **않음**
- RigVM에서 멀티스레드 실행
- 연속 메모리 레이아웃으로 캐시 효율적

### 주의할 점
- UAF는 아직 Experimental -- 최적화가 완료되지 않음
- PublicVariablesProxy가 매 프레임 dirty 데이터를 복사
- 향후 더블 버퍼링으로 개선 예정

---

## 10.4 버전 호환성 주의

| 항목 | UE 5.6 | UE 5.7 |
|------|--------|--------|
| 플러그인 접두사 | AnimNext | UAF |
| System 이름 | Module | System |
| Motion Matching 노드 | 미제공 (커스텀 필요) | 기본 제공 |
| Chooser 연동 | DataInterfaceInstance 필요 | 직접 바인딩 가능 |

> UE 버전이 다르면 API가 크게 다릅니다. 5.6 자료는 5.7에서 그대로 적용되지 않을 수 있습니다.

---

## 10.5 Epic Games의 공식 입장

> "We do not recommend that projects use the technology because, even since showing it at Orlando, we have made significant changes to it."
> -- DDeVoe (Epic Games)

- 프로덕션 프로젝트에는 기존 ABP + Motion Matching 조합이 안전
- UAF는 학습/실험 목적으로만 사용 권장
- UE 5.8에서 첫 공식 데모 예정

---

## 10.6 자주 저장하기

UAF 에디터는 아직 안정적이지 않으므로:
- **Ctrl+S**를 자주 눌러 저장
- 복잡한 변경 전 백업 생성
- 크래시 후 `Saved/Logs/` 폴더의 로그 확인

---

[<- 이전: 기술 아키텍처](./09_ARCHITECTURE.md) | [목차](./00_INDEX.md) | [다음: 참고 자료 ->](./APPENDIX_RESOURCES.md)
