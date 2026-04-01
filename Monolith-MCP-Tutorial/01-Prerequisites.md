# 1. 사전 준비

## 1.1 Unreal Engine 5.7 설치

### Epic Games Launcher에서 설치

1. **Epic Games Launcher** 실행
2. 왼쪽 메뉴에서 **"Unreal Engine"** 클릭
3. 상단 **"Library"** 탭 선택
4. **"+"** 버튼 클릭 → 버전 목록에서 **5.7** 선택
5. **"Install"** 클릭
6. 설치 경로 확인 (기본: `C:\Program Files\Epic Games\UE_5.7`)
7. 설치 완료까지 대기 (약 30~60분)

### 기존 프로젝트를 5.7로 업그레이드하는 경우

```
⚠️ 주의: 업그레이드 전 반드시 프로젝트를 백업하세요!

1. 프로젝트 폴더 전체를 복사하여 백업
2. .uproject 파일을 우클릭 → "Switch Unreal Engine version" → 5.7 선택
3. 또는 .uproject 파일을 텍스트 에디터로 열어서:
   "EngineAssociation": "5.7" 로 변경
4. 프로젝트 실행 → "이 프로젝트를 변환하시겠습니까?" → 예
```

### 새 프로젝트 만들기 (권장 - 테스트용)

1. Epic Games Launcher → **Launch** (5.7)
2. **Games** → **Third Person** 템플릿 선택
3. **Blueprint** 선택 (C++ 아닌)
4. 프로젝트 이름: `MonolithTest`
5. 위치: `C:\Users\ohmil\OneDrive\문서\Unreal Projects\`
6. **Create** 클릭

> 💡 테스트용으로 새 프로젝트를 만든 후, 익숙해지면 기존 프로젝트에 적용하는 것을 권장합니다.

## 1.2 Claude Code 설치 확인

```bash
# Claude Code 버전 확인
claude --version

# 설치 안 되어 있다면:
npm install -g @anthropic-ai/claude-code
```

## 1.3 Git 설치 확인

```bash
# Git 버전 확인
git --version

# 설치 안 되어 있다면:
# https://git-scm.com/downloads 에서 다운로드
```

## 1.4 (선택) Python 3.10+ 설치

C++ 프로젝트의 소스 코드를 AI에게 인덱싱시키려면 Python이 필요합니다.
Blueprint 전용 프로젝트라면 불필요합니다.

```bash
# Python 버전 확인
python --version
# Python 3.10 이상이어야 함
```

## 체크리스트

다음 단계로 넘어가기 전에 확인하세요:

- [ ] Unreal Engine 5.7이 설치됨
- [ ] UE 5.7 프로젝트가 있음 (새로 만들기 또는 업그레이드)
- [ ] Claude Code가 설치됨
- [ ] Git이 설치됨
- [ ] (선택) Python 3.10+

---
[다음: Monolith 설치 →](02-Installation.md)
