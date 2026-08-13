---
name: tune-abp
description: AnimBP 튜닝 에이전트(animbp-tuner) 호출 — Inspector 처방 필요
---

# /tune-abp — AnimBP 튜닝 에이전트 호출

Inspector 가 제시한 처방을 **실제 ABP 에셋에 적용**. Monolith HTTP API 로 CDO 변수 / 노드 프로퍼티 mutate + 에셋 save + 재dump 로 before/after 비교.

## 호출 형식

사용자 발화 예:
- `/tune-abp 방금 진단한 처방 적용`
- `/tune-abp PelvisSettings.MaxOffset 을 10 → 8 로 변경`
- `/tune-abp IsTransition gate 추가 (BlendListByBool 분기)`

## ⚠ 사전 조건 (강제)

1. **Inspector 처방이 반드시 선행** — 단독 호출 금지. `/inspect-abp` 보고서 없으면 거부
2. **dry-run 옵션 명시** — 어떤 변경이 일어날지 사전 출력
3. **백업 자동 생성 (필수)** — 변경 직전 다음 한 줄 실행 후 결과 path 를 prompt 에 포함:
   ```bash
   py scripts/abp_backup.py backup <asset> <간략한_라벨>
   ```
   - 5종 dump 묶음 (abp_info/state_machines/transitions/variables) `.claude/state/backups/<ASSET>/<TIMESTAMP>_<label>/` 보존
   - 변경 후 문제 발생 시 `py scripts/abp_backup.py restore <asset> <label> --apply` 로 변수 default 복원
   - 노드 추가/삭제, transition rule chain 변경은 자동 복원 불가 → 사용자 에디터 수동
4. **save_asset 실패 가능성 알림** — P4 잠금이면 사용자 Ctrl+S 안내 ([[project-pc01-psd-gmt-continuing-bias]] 학습)

## 실행 지침

Agent tool 의 `subagent_type=animbp-tuner` 로 호출. prompt 에 다음 포함:

1. **Inspector 처방 spec** (필수): JSON 또는 명확한 단계별 변경 항목
2. **자산 경로**: 변경 대상 ABP path
3. **백업 위치 (현재 dump)**: dumps/sm/<ASSET>_*.json 최근 dump 시각
4. **검증 후 비교 대상**: 동일 dump 재실행 결과로 diff

## Tuner 가 자동 수행

- before-dump 보존
- 변경 적용 (batch_execute 권장)
- compile_blueprint + validate_blueprint
- save_asset (실패 시 사용자에게 알림)
- after-dump + diff
- 결과 보고 (변경 항목 + side effect 가능성)

## 시각 검증 (선택, 사용자 호소 영역에 권장)

[[feedback-visual-mesh-over-anim-rec]] — "시각이 진짜 기준" 원칙. ANIM_REC 수치 검증만으로 부족한 경우:

```bash
py scripts/screenshot.py --before-after <label> --copy dumps/screenshots
```
- 사용자 PIE 시작 → before 캡처 → 변경 적용 → after 캡처
- AI 가 두 PNG `Read` 로 multimodal 비교

상세: [[reference-visual-verification]]

## 사용 안 할 때

- 처방 없이 사용자가 직접 값 변경하고 싶다 → 직접 monolith.blueprint_query 호출 (또는 scripts/monolith_helpers.py)
- 위험 큰 영역 (SM transition rule 전체 교체 등) → 임시 테스트 ABP 에서 PoC 먼저

## 호출 후 자동 후속

- save 실패 시: 사용자에게 P4 Check-Out + Ctrl+S 안내
- after-dump 가 before 와 동일 (변경 안 적용) → 진단 실패 원인 분석
- side effect 발견 (compile errors > 0) → 즉시 rollback 제안

## 관련 메모리

- [[reference-sanjuk-agents]]
- [[reference-animgraph-node-editing]] — BlendListByBool IsTransition gate 패턴
- [[reference-monolith-animgraph-editing-limits]] — node_type / save_asset / Chooser 한계
