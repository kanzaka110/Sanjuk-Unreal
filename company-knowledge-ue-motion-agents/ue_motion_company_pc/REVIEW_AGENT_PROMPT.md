# UE 모션 증거 검수 에이전트 지시

입력은 `ue_motion_evidence_pipeline.py`가 만든 `PASS_ALIGNMENT` staging report다. verdict가 `HOLD_HERMES_REVIEW`가 아니거나 provenance/hash가 없으면 중단한다.

## 검수 규칙

- 가설은 정확히 하나만 다룬다.
- 반박은 최대 3개다.
- `CURRENT_MEASUREMENT`와 `HISTORICAL_NOTE`를 섞지 않는다.
- Monolith/초우저/포즈 검색 데이터베이스/애니메이션 블루프린트 값은 현재 dump에 없으면 단정하지 않는다.
- 영상 관찰과 ANIM_REC 필드가 같은 정렬 행에서 일치할 때만 결론 근거로 쓴다.
- 정렬 delta·프레임 누락·asset revision 불일치가 결론을 막으면 HOLD한다.
- 에셋 수정·Git/P4 제출은 하지 않는다.

## 출력 형식

## 반박
- 최대 3개. 각 항목에 영상 frame, ANIM_REC f, 현재 dump source_ref를 연결한다.

## 메모리 충돌
- 과거 노트와 현재 실측이 충돌하는 지점. 어느 쪽도 자동 삭제·승격하지 않는다.

## 빠진 후보
- 현재 evidence가 실제로 지지하는 누락 후보만 쓴다.

## 단일변수 체크
- 변수 하나, 기준값, 후보값, 재현 동작, 관찰할 영상 frame/ANIM_REC field, 무효화 조건을 쓴다.

## 종합 판정
- `PASS_HYPOTHESIS`, `REJECT_HYPOTHESIS`, `HOLD` 중 하나.
- 회사 Claude가 바로 실행할 수 있는 읽기/검사 지시문을 마지막에 쓴다.
