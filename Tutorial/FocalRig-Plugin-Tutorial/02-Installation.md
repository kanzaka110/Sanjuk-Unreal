# 2. 설치 및 프로젝트 설정

## 2.1 사전 준비

### 필수 사항

```
✅ Unreal Engine 5.3 이상 설치 (5.5+ 권장)
✅ UE5 프로젝트 생성 완료
✅ Epic Games 계정 (Fab 구매용)
```

### 권장 프로젝트 설정

테스트용으로 **Third Person 템플릿** 프로젝트를 새로 만드는 것을 권장합니다.

```
1. Epic Games Launcher → UE5 Launch
2. Games → Third Person 템플릿 선택
3. Blueprint 선택
4. 프로젝트 이름: FocalRigTest
5. Create 클릭
```

> 💡 Third Person 템플릿에는 이미 Mannequin 캐릭터와 기본 애니메이션이 포함되어 있어 FocalRig 테스트에 적합합니다.

## 2.2 Fab에서 FocalRig 구매 및 다운로드

### Step 1: Fab 접속

1. 브라우저에서 [fab.com](https://www.fab.com/) 접속
2. Epic Games 계정으로 로그인

### Step 2: FocalRig 검색

1. 검색창에 **"FocalRig"** 입력
2. **FocalRig — Procedural Look & Aim** 제품 선택
3. 제품 페이지에서 상세 정보 확인

### Step 3: 구매 및 라이브러리 추가

1. **구매(Buy)** 또는 **장바구니에 추가** 클릭
2. 결제 진행
3. 구매 완료 후 **라이브러리(Library)**에 추가됨

### Step 4: 프로젝트에 추가

```
방법 A: Fab 런처 (권장)
1. Fab 런처 또는 UE 에디터 내 Fab 브라우저 열기
2. "My Library" (내 라이브러리) 이동
3. FocalRig 찾기 → "Add to Project" 클릭
4. 대상 프로젝트 선택 → 추가

방법 B: 수동 설치
1. Fab에서 FocalRig 플러그인 파일 다운로드
2. 다운로드한 파일을 프로젝트의 Plugins 폴더에 복사:
   [프로젝트 폴더]/Plugins/FocalRig/
3. 에디터 재시작
```

## 2.3 플러그인 활성화 확인

### Control Rig 플러그인 확인

FocalRig은 UE5의 **Control Rig** 시스템 위에서 동작하므로, Control Rig 플러그인이 활성화되어 있어야 합니다.

```
1. UE 에디터 메뉴: Edit → Plugins
2. 검색창에 "Control Rig" 입력
3. "Control Rig" 플러그인이 ✅ 활성화(Enabled) 상태인지 확인
4. 비활성화되어 있다면 체크박스를 클릭하여 활성화
5. 에디터 재시작 필요할 수 있음
```

> ⚠️ Control Rig은 UE5에 기본 포함되어 있지만, 프로젝트에 따라 비활성화되어 있을 수 있습니다. 반드시 확인하세요.

### FocalRig 플러그인 확인

```
1. Edit → Plugins
2. 검색창에 "FocalRig" 입력
3. FocalRig 플러그인이 목록에 나타나는지 확인
4. ✅ Enabled 체크
5. 에디터 재시작
```

### 확인 방법

플러그인이 정상적으로 설치되었는지 확인하는 가장 확실한 방법:

```
1. Content Browser에서 우클릭
2. Animation → Control Rig → Control Rig Blueprint 생성
3. Control Rig 에디터에서 우클릭 → 노드 추가
4. "FocalRig" 또는 "Aim Chain" 검색
5. FocalRig 노드가 목록에 나타나면 설치 성공!
```

## 2.4 프로젝트 설정 확인

### .uproject 파일 확인

FocalRig 설치 후, 프로젝트 파일(`.uproject`)에 플러그인 의존성이 추가됩니다:

```json
{
  "Plugins": [
    {
      "Name": "ControlRig",
      "Enabled": true
    },
    {
      "Name": "FocalRig",
      "Enabled": true
    }
  ]
}
```

### Build.cs 확인 (C++ 프로젝트인 경우)

C++ 프로젝트에서 FocalRig API를 직접 사용하려면, 모듈 의존성을 추가해야 합니다:

```csharp
// [프로젝트명].Build.cs
PublicDependencyModuleNames.AddRange(new string[]
{
    "Core",
    "CoreUObject",
    "Engine",
    "ControlRig",
    "FocalRig"    // FocalRig 모듈 추가
});
```

> 💡 Blueprint 전용 프로젝트라면 Build.cs 수정은 필요 없습니다. 플러그인 활성화만으로 충분합니다.

## 2.5 설치 문제 해결 (트러블슈팅)

### 문제 1: FocalRig 노드가 검색되지 않음

```
원인: 플러그인이 활성화되지 않았거나 설치 경로가 잘못됨

해결:
1. Edit → Plugins에서 FocalRig가 Enabled인지 확인
2. 에디터를 완전히 종료 후 재시작
3. Plugins 폴더에 FocalRig 폴더가 올바르게 있는지 확인
4. 프로젝트의 Intermediate 폴더 삭제 후 재빌드
```

### 문제 2: 컴파일 에러 발생

```
원인: UE 버전 호환성 문제

해결:
1. FocalRig이 지원하는 UE 버전인지 확인
2. Fab 제품 페이지에서 호환 버전 목록 확인
3. 필요 시 UE 버전 업데이트
```

### 문제 3: Control Rig 플러그인 관련 에러

```
원인: Control Rig이 비활성화되어 있음

해결:
1. Edit → Plugins → "Control Rig" 검색
2. Control Rig 활성화
3. 에디터 재시작
4. 다시 FocalRig 활성화 시도
```

## 2.6 설치 확인 테스트

설치가 완료되었는지 간단하게 확인해봅시다:

### 테스트 1: 노드 검색

```
1. Content Browser → 우클릭 → Animation → Control Rig
2. 새 Control Rig 에셋 생성 (이름: CR_FocalRigTest)
3. 더블클릭하여 Control Rig 에디터 열기
4. Rig Graph에서 우클릭 → 노드 검색
5. "Aim Chain" 검색 → 노드가 나타나면 성공!
6. "Eye Aim" 검색 → 노드가 나타나면 성공!
7. "Recoil" 검색 → 노드가 나타나면 성공!
```

### 테스트 2: Quick Setup 확인

```
1. 위에서 만든 Control Rig에 Aim Chain 노드를 추가
2. 노드의 Details 패널에서 "Quick Setup" 드롭다운 확인
3. 드롭다운에 스켈레톤 기반 설정 옵션이 나타나면 성공!
```

## 체크리스트

다음 단계로 넘어가기 전에 확인하세요:

- [ ] Fab에서 FocalRig을 구매/다운로드함
- [ ] FocalRig 플러그인이 프로젝트에 설치됨
- [ ] Control Rig 플러그인이 활성화됨
- [ ] FocalRig 플러그인이 활성화됨
- [ ] Control Rig 에디터에서 FocalRig 노드가 검색됨
- [ ] 에디터 재시작 완료

---
[← 이전: FocalRig이란?](01-What-Is-FocalRig.md) | [다음: 핵심 개념 이해하기 →](03-Core-Concepts.md)
