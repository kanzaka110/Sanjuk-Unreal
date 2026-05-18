---
name: feedback-visual-mesh-over-anim-rec
description: "ANIM_REC 수치만 보고 \"처방 성공\" 판단하지 말 것. 사용자가 보는 mesh 시각적 동작이 진짜 검증 기준. 2026-05-15 일련의 처방 실패에서 학습."
metadata: 
  node_type: memory
  type: feedback
  date: 2026-05-15
  originSessionId: 9dcc5175-e415-47ad-96d0-959bb0242e16
---

# Mesh 시각 동작이 진짜 검증 기준

## 룰
[ANIM_REC] 로그의 trd / clip / sc 값만 보고 "처방 성공" 판단하면 안 됨. **사용자가 PIE 화면에서 보는 mesh 시각 동작이 진짜 검증 기준**.

수치 패턴이 완벽해도 mesh 동작이 어색하면 처방 실패. 반대로 수치는 이상해 보여도 mesh 동작이 자연스러우면 그게 정답.

## Why
2026-05-15 일련의 처방 작업에서:
- ANIM_REC: "transition 시점 trd=0" 완벽 → "처방 성공" 보고
- 사용자: "mesh가 이상한데?" — 우리 가설 자체가 잘못
- 진실: 사용자 의도는 transition 시점에도 mesh가 raw 회전해야 자연스러움. trd=0 는 추가 회전을 차단해버려 mesh 부자연스럽게 됨

ANIM_REC trd=0 라는 게 mesh 정지 의미가 아니라 "추가 회전 없음" 의미. root motion 만으로 mesh 회전. 그러나 사용자 시각적 의도는 root motion + 추가 회전 둘 다 자연스럽게 합쳐지는 것.

## How to apply
- 새 처방 적용 후 ANIM_REC 분석 결과를 **사용자 시각적 평가와 함께** 확인
- 사용자가 "이상해" "정상 안 됨" 호소 시 우리 수치 분석이 일치해도 가설 의심
- 가능하면 처방 적용 전에 사용자가 원하는 mesh 동작 명확히 — 글자, 영상, 비교 케이스
- "trd=0", "회전 차단", "root motion만" 같은 단순한 해석 위험 — 사용자가 원하는 건 보통 더 복잡하고 미묘함

## 관련
- [[pc01-transition-gate-user-corrected]] — 사용자가 직접 wiring 정정한 결과 (정답)
- [[pc01-mm-pipeline]] (MM 분석 일반 원칙)
