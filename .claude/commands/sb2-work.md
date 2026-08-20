---
description: Jira·Confluence·ShiftUp Slack에서 승호 업무를 검색·통합·관리
argument-hint: scan | sync | apply | status
allowed-tools: mcp__claude_ai_Atlassian_Rovo__atlassianUserInfo, mcp__claude_ai_Atlassian_Rovo__getAccessibleAtlassianResources, mcp__claude_ai_Atlassian_Rovo__search, mcp__claude_ai_Atlassian_Rovo__searchConfluenceUsingCql, mcp__claude_ai_Atlassian_Rovo__getConfluencePage, mcp__claude_ai_Atlassian_Rovo__getConfluencePageFooterComments, mcp__claude_ai_Atlassian_Rovo__getConfluencePageInlineComments, mcp__claude_ai_Atlassian_Rovo__getPagesInConfluenceSpace, mcp__claude_ai_Atlassian_Rovo__createConfluencePage, mcp__claude_ai_Atlassian_Rovo__updateConfluencePage, mcp__claude_ai_Atlassian_Rovo__createConfluenceFooterComment, mcp__claude_ai_Atlassian_Rovo__searchJiraIssuesUsingJql, mcp__claude_ai_Atlassian_Rovo__getJiraIssue, mcp__claude_ai_Atlassian_Rovo__getTransitionsForJiraIssue, mcp__claude_ai_Atlassian_Rovo__transitionJiraIssue, mcp__claude_ai_Atlassian_Rovo__addCommentToJiraIssue, mcp__claude_ai_Slack__slack_read_user_profile, mcp__claude_ai_Slack__slack_search_public_and_private, mcp__claude_ai_Slack__slack_read_thread, mcp__claude_ai_Slack__slack_send_message, mcp__claude_ai_Slack__slack_send_message_draft
---

# SB2 Work Agent

모드: `$ARGUMENTS`. 비어 있으면 `scan`으로 실행한다.

## 목적

ShiftUp Jira·Confluence·Slack에서 채승호가 실제로 해야 하는 일을 찾아 하나의 업무 목록으로 통합하고, 근거가 명확한 안전한 변경만 원본에 반영한다. 모든 원문과 인증은 회사 PC의 기존 Claude MCP 안에 남긴다.

## 기존 owner 경로

- Atlassian: `claude_ai_Atlassian_Rovo` MCP. 신규 API 토큰을 요구하지 않는다.
- Slack: `claude_ai_Slack` MCP. 승호 계정을 가장하지 않는다.
- 업무판: Confluence SB2 공간의 `[SB2] 채승호 업무 인박스` 페이지.
- 기존 페이지가 없으면 `sync`에서만 SB2 공간 또는 승호 개인 공간을 확인한 뒤 생성한다. 임의 공간에는 만들지 않는다.

## 시작 시 신원·리소스 확인

1. `atlassianUserInfo`와 `slack_read_user_profile`로 현재 승호 계정 ID·표시 이름을 확인한다.
2. `getAccessibleAtlassianResources`로 `shiftupcorp.atlassian.net` cloud ID를 읽는다. 문자열 도메인과 UUID 중 도구가 반환한 값을 사용한다.
3. Confluence SB2 공간과 업무 인박스 페이지를 검색한다.
4. 계정·cloud ID·SB2 공간 중 하나라도 확인되지 않으면 변경하지 말고 `BLOCK`으로 끝낸다.

## 수집

### Jira

`searchJiraIssuesUsingJql`로 최소 다음 범위를 검색한다.

```text
assignee = currentUser() AND resolution = Unresolved ORDER BY priority DESC, due ASC, updated DESC
```

추가로 최근 30일 안에 승호가 watcher·요청 대상이 된 SB2 이슈를 `search`로 보완한다. 후보마다 `getJiraIssue`로 현재 담당자·상태·기한·우선순위·최근 댓글을 확인한다.

### Confluence

`search`와 `searchConfluenceUsingCql`로 SB2 공간의 최근 30일 페이지에서 다음을 찾는다.

- 승호에게 할당된 미완료 액션 아이템
- 회의록의 `채승호`, `승호`, 확인된 계정 멘션과 행동 요청
- 승호가 하기로 명시한 약속

후보 페이지는 `getConfluencePage`로 본문과 버전을 읽고, 필요한 경우 댓글도 확인한다. 단순 이름 등장·참조·완료된 체크박스는 제외한다.

### Slack

`slack_search_public_and_private`로 최근 30일 범위에서 승호의 확인된 멘션·이름과 `부탁`, `확인`, `수정`, `공유`, `언제`, `TODO`, `액션` 등 직접 요청 표현을 조합해 검색한다. 후보는 `slack_read_thread`로 전체 스레드를 확인한다.

다음은 제외한다.

- 공지·참조용 멘션
- 이미 취소·완료된 요청
- 다른 담당자에게 확정 배정된 요청
- 질문인지 업무 요청인지 불분명한 문장
- 봇·자동 알림

## 통합 스키마

각 항목을 다음 필드로 정규화한다.

```text
work_id | title | next_action | status | priority | due_at
requester | assignee | source_refs[] | source_urls[]
reason | confidence | last_verified_at | proposed_actions[]
```

중복 우선순위:

1. Jira 키가 같으면 하나로 통합
2. 같은 Confluence 페이지/인라인 작업 ID면 통합
3. Slack 스레드가 Jira 키나 Confluence URL을 언급하면 해당 항목에 결합
4. 제목 유사도만으로 자동 병합하지 말고 `확인 필요`로 둔다

우선순위는 명시적 기한·Jira 우선순위·blocking 여부·요청자 명시성을 사용한다. 추측한 기한은 만들지 않는다.

## 모드

### `scan`

읽기만 수행한다. 결과를 `긴급 / 오늘 / 이번 주 / 대기 / 확인 필요`로 출력하고 원본 링크와 판정 근거를 붙인다. 외부 변경 금지.

### `sync`

`scan` 후 Confluence 업무 인박스 페이지를 갱신한다.

- 먼저 현재 페이지와 버전을 읽는다.
- 기존 수동 메모·완료 기록을 보존한다.
- `자동 동기화 영역`만 교체한다.
- `updateConfluencePage` 호출 후 다시 `getConfluencePage`로 버전 증가와 핵심 work_id 존재를 확인한다.
- 동일 입력이면 추가 버전 생성 없이 종료한다.

### `apply`

`sync` 후 다음 변경만 실행한다.

- Jira: 담당자가 승호이고 현재 상태가 readback과 일치할 때만 허용된 `진행 중` 전환
- Jira: 업무 인박스 링크와 현재 판단 근거를 댓글로 1회만 추가
- Confluence: 자동 동기화 영역만 갱신
- Slack: 원래 요청 스레드에 봇/Claude 명의로 접수·상태 링크를 1회만 답변

다음은 자동 실행하지 않는다.

- Jira 완료·종료·삭제, 담당자·기한 변경
- Confluence 페이지 삭제 또는 자동 영역 밖 본문 수정
- Slack 새 공개 채널 메시지·대량 전송
- 승호 이름을 가장한 답변

모든 변경은 `현재값 확인 → 한 번 실행 → 원본 재조회`로 끝낸다. 예상 상태가 다르면 재시도하지 말고 `HOLD`로 기록한다.

### `status`

업무 인박스와 연결된 Jira·Confluence·Slack 원본을 다시 읽어 `진행중 / 멈춤 / 완료 / 불일치`를 판정한다. 원본이 확인되지 않은 항목을 완료 처리하지 않는다.

## 출력

```text
[SB2 업무 에이전트]
상태: PASS | HOLD | BLOCK
신규 N / 변경 N / 완료 확인 N / 확인 필요 N

[긴급]
- 제목 — 다음 행동 — 기한 — 원본

[적용]
- 시스템 / 대상 / 변경 / readback

[확인 필요]
- 항목 / 불명확한 점 / 원본
```

토큰·cookie·세션·원문 전체·비공개 대화 전문은 출력이나 `/push`에 넣지 않는다.
