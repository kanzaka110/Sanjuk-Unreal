# briefing.py STEP 2 Haiku 모델 변경 패치

> 적용 대상: `desktop-tutorial/briefing/briefing.py`
> 로컬 PC에서 적용 후 GitHub에 push

## 변경 내용

### 수정 사항
STEP 2 (메타데이터 추출) API 호출에서 모델을 `claude-sonnet-4-6` → `claude-haiku-4-5-20251001`로 변경

### 찾아야 할 코드 패턴

`briefing.py`에서 STEP 2 메타데이터 추출 부분을 찾습니다.
보통 아래와 같은 패턴:

```python
# STEP 2: 메타데이터 추출 (또는 유사한 주석)
response = client.messages.create(
    model="claude-sonnet-4-6",  # ← 이 줄을 변경
    ...
)
```

### 변경 방법

```python
# 변경 전
model="claude-sonnet-4-6"

# 변경 후
model="claude-haiku-4-5-20251001"
```

### 주의사항

- **STEP 1 (웹검색)**과 **STEP 3 (본문 생성)**의 모델은 `claude-sonnet-4-6` 유지
- STEP 2만 변경 — 단순 JSON 추출 작업이므로 Haiku로 충분
- 예상 비용 절감: ~30% (STEP 2가 전체의 약 1/3)

### 적용 절차

1. 로컬 PC에서 `desktop-tutorial/briefing/briefing.py` 열기
2. STEP 2 메타데이터 추출 부분의 `model=` 파라미터 변경
3. 테스트: `python briefing.py --category "GASP"` 로 1건 실행
4. 정상 동작 확인 후 `git commit -m "perf: STEP 2 메타데이터 추출 모델을 Haiku로 변경"` && `git push`
