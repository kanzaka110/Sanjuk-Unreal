# /hermes — 대화 중간 실시간 Hermes 공유 (Slack 직송)

현재 세션에서 진행 중인 작업/분석을 **압축 다이제스트**로 만들어 **Slack 비공개 채널(Hermes 봇방 연동)에 즉시 전송**한다.
전송은 `scripts/hermes_send.py`(Hermes 봇 토큰, .env)가 수행 — 사용자 손 댈 일 없음.

참고: 매 턴 자동 공유는 Stop 훅(`scripts/hermes_auto_share.py`, `.claude/settings.json`)이 이미 수행한다.
/hermes는 **자동공유보다 정제된 요약**을 보내고 싶을 때 수동으로 쓴다.

`/evidence`(완결된 증거 패킷)와 달리, **진행 중인 맥락을 가볍게 던지는 용도** — 결론 전이라도 보낸다.

## 절차

1. **다이제스트 생성** — 현재 대화에서 아래 형식으로 압축 (3,500자 이내 목표):

```
> **[Hermes 실시간 공유]** YYYY-MM-DD HH:MM
> 작업: [한 줄 — 무엇을 하는 중인지]
> 지금까지 확인된 것: [실측/관찰 사실만, 항목당 1줄]
> 현재 가설/방향: [있으면. 미확정이면 "미확정" 명시]
> 다음 단계: [예정 작업]
> (요청 있을 때만) 질문: [Hermes에게 묻는 것]
```

2. **전송** — 다이제스트를 `scripts/_hermes_msg.txt` 에 utf-8 저장 후:
   ```
   py scripts/hermes_send.py --file scripts/_hermes_msg.txt
   ```
   (인라인 문자열 인자 금지 — 한글/멀티라인 이스케이프 깨짐 방지를 위해 파일 경유)

3. **보고** — 전송 결과(청크 수) 한 줄 + 다이제스트 본문도 화면에 출력 (검토용). 실패 시 `.env`의 SLACK_BOT_TOKEN / HERMES_SLACK_CHANNEL 확인 안내.

## 인자 처리

- `/hermes` 단독 → 현재 세션 전체 맥락 다이제스트
- `/hermes <주제>` → 해당 주제에 한정한 다이제스트
- `/hermes 질문: ...` → 다이제스트 + 질문 줄 포함 (검증 요청)

## 보안 원칙 (evidence.md와 동일)

- 회사 코드 / 토큰 / 비공개 원문 **대량 덤프 금지**
- 에셋 경로 / 파라미터(전→후) / 노드명 / 판정 결과 중심으로 압축
- 로그는 판단 근거 라인만 발췌

## 인프라 구성 (2026-06-11 확정)

- 전송: `scripts/hermes_send.py` — Hermes 봇 자신의 Slack 토큰으로 chat.postMessage. 봇은 자기가 멤버인 방에 항상 쓸 수 있어 회사 워크스페이스 정책 무관.
- 자동: `scripts/hermes_auto_share.py` — Stop 훅이 매 턴 마지막 응답을 transcript에서 추출(토큰 0). 필터: 300자 미만 skip / 직전과 동일 skip. 로그 `scripts/_hermes_auto.log`.
- claude.ai Slack 커넥터는 비공개 채널 접근 불가(워크스페이스 권한 제한) — 사용하지 않음.
- 텔레그램 직송(Telethon)은 봇→봇 차단 + 셋업 부담으로 폐기.

## 원칙

- **Hermes 응답은 ground truth 아님** — 지적은 실측 재확인 후 채택/기각 ([[reference-hermes-reviewer-role]])
- 결론 확정 시점의 정식 검증은 `/evidence` 사용 (후보 3개 + 반증 강제). /hermes는 그 전 단계의 가벼운 공유 채널
- 검수 지적을 실측 판정하면 [[reference-hermes-review-outcomes]] 에 1줄 기록 (기존 룰 유지)
