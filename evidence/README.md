# Evidence 패킷 저장소

`/evidence`로 생성한 원인 분석 패킷을 **Hermes 학습용으로 영속**하는 곳.

## 흐름
```
/evidence (출력) → 사용자가 보존 결정 → evidence/YYYY-MM-DD-<slug>.md 저장
  → /push (git) → GCP repo → export-for-hermes.sh #12 → hermes-export/ue_evidence_packets.txt
  → 매시간 rsync → Hermes 학습 (우리 추론 패턴: 후보+반증+폐기이유)
```

## 명명
- `YYYY-MM-DD-<짧은-슬러그>.md` (예: `2026-05-26-bf-pivot-chooser-dup.md`)
- 내용은 `/evidence` 패킷 포맷 그대로 (증상 / 관찰 / 후보3+반증 / 결론 / 검증).

## 원칙
- **선택 보존**: 모든 패킷을 저장하진 않음. 재사용 가치 있는 원인분석만.
- **보안**: 회사 코드/토큰 원문 금지. 에셋 경로·파라미터(전→후)·판단 근거만.
- **신뢰도 태그**: 결론에 `✅실측`/`⚠가설` 태그 ([[reference-memory-status-tags]] 컨벤션).
