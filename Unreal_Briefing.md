# 🎮 UE 애니메이션 데일리 브리핑 시스템

매일 오전 9시 KST에 언리얼 엔진 애니메이션 관련 최신 정보를 수집하여
Notion 데이터베이스에 자동으로 브리핑 페이지를 생성합니다.

---

## 📂 프로젝트 위치

| 항목 | 경로 / URL |
|------|-----------|
| **로컬 코드** | `C:\Users\ohmil\OneDrive\바탕 화면\desktop-tutorial\` |
| **GitHub repo** | `kanzaka110/desktop-tutorial` (private) |
| **Notion DB** | [🎮 UE 애니메이션 데일리 브리핑](https://www.notion.so/4fd756cb968d4439b9e80bbc69184a57?v=6ddb9c42592f4fa8a06866e472aab603) |

---

## 📁 핵심 파일 구조

```
desktop-tutorial/
├── .github/workflows/
│   └── ue-animation-briefing.yml    ← GitHub Actions (매일 9시 KST)
├── briefing/
│   ├── briefing.py                  ← 메인 스크립트 (Claude API + Notion)
│   ├── requirements.txt             ← anthropic, notion-client, python-dotenv
│   ├── .env.example                 ← 로컬 테스트용 환경변수 템플릿
│   └── SETUP.md                     ← 설정 가이드
└── README.md
```

---

## 🚀 실행 방법

### Claude Code에서 바로 실행

```bash
# 1개 카테고리 자동 선택
export PATH="/c/Program Files/GitHub CLI:$PATH"
GH_TOKEN="<토큰>" gh workflow run ue-animation-briefing.yml \
  --repo kanzaka110/desktop-tutorial -f count=1

# 특정 카테고리
-f category="Control Rig"

# 전체 10개 카테고리 재생성
-f all_categories=true -f force=true

# 버전별 분리 (카테고리 × UE 5.5/5.6/5.7/5.8+)
-f all_categories=true -f force=true -f per_version=true
```

### 자동 실행
- **스케줄**: 매일 오전 9:00 KST (UTC 00:00)
- **기본**: 날짜 시드로 3개 카테고리 자동 선택

---

## 📋 10개 카테고리

| # | 카테고리 | 설명 |
|---|---------|------|
| 1 | Animation Blueprint | AnimGraph, State Machine, Blend Space |
| 2 | Control Rig | 런타임 리깅, IK, 절차적 애니메이션 |
| 3 | Motion Matching | 데이터베이스 기반 포즈 매칭 |
| 4 | UAF/AnimNext | 차세대 애니메이션 프레임워크 |
| 5 | MetaHuman | 고품질 디지털 휴먼, 페이셜 애니메이션 |
| 6 | Sequencer | 시네마틱, 키프레임 애니메이션 편집기 |
| 7 | Live Link | 모션 캡처 실시간 스트리밍 |
| 8 | ML Deformer | 머신러닝 기반 캐릭터 변형 |
| 9 | GASP | Game Animation Sample Project |
| 10 | Mover Plugin | 차세대 캐릭터 이동 컴포넌트 |

---

## 🔧 아키텍처 (3단계 생성)

```
[STEP 1] 웹 검색
  Claude API + web_search (8회) → 최신 UE 애니메이션 정보 수집

[STEP 2] 메타데이터 추출
  Claude API → 제목/요약/태그 JSON

[STEP 3] 본문 생성
  Claude API → Notion 마크다운 (이전 잘 만든 페이지 형식 참조)
  → Notion 네이티브 블록 변환 (테이블, 코드블록, 콜아웃, 구분선 지원)
  → 미지원 코드 언어 자동 보정 (plain text 폴백)
```

---

## 🆕 신규 정보 표기 시스템

| 시점 | 동작 |
|------|------|
| 오전 9시 브리핑 시작 | 어제 이전 페이지의 `🆕` 제목 표기 제거 + `🆕 신규` 체크박스 OFF |
| 새 페이지 생성 | 제목에 `🆕` 추가 + `🆕 신규` 체크박스 ON |
| 본문 내 | 최근 1주 이내 새 정보 섹션에 🆕 이모지 표기 |
| 다음날 9시 | 어제 페이지의 🆕 자동 제거 → 새 브리핑에 🆕 부여 |

**Notion DB 속성**: `🆕 신규` (checkbox) — 테이블 뷰에서 필터/정렬 가능

---

## ⚡ 워크플로우 옵션

| 옵션 | 설명 |
|------|------|
| `count` | 자동 선택 카테고리 수 (기본 3) |
| `category` | 특정 카테고리 지정 |
| `all_categories` | 전체 10개 카테고리 실행 |
| `force` | 중복 체크 무시 — 재생성 |
| `per_version` | UE 버전별 개별 페이지 생성 (5.5/5.6/5.7/5.8+) |

---

## 🔑 GitHub Secrets (등록 완료)

| Secret | 용도 |
|--------|------|
| `ANTHROPIC_API_KEY` | Claude API (sk-ant-...) — **종량제 과금** (Max 플랜과 별도) |
| `NOTION_API_KEY` | Notion 통합 토큰 |
| `NOTION_DATABASE_ID` | `4fd756cb968d4439b9e80bbc69184a57` |

---

## 💰 API 비용 참고

- Claude Code **Max 플랜** (월 $100)과 **Anthropic API 크레딧은 별개** 과금
- briefing.py는 Anthropic API를 직접 호출 → 종량제 크레딧 필요
- 모델: `claude-sonnet-4-6` (1건당 약 3회 API 호출)
- 비용 절감: 모델을 Haiku로 변경하면 ~10배 저렴

---

## ⚠️ 주의사항

- Anthropic API **분당 30,000 입력 토큰 제한** → 카테고리 간 90초 대기 + 실패 시 최대 3회 재시도
- 전체 10개 카테고리 실행 시 약 **45~60분** 소요
- 개별 실행 권장 (rate limit 방지): 카테고리별 `-f category="..."` 사용
- Notion DB에 **"주식 분석 봇" 통합이 연결**되어 있어야 함
- Notion 코드블록 언어 검증 적용 (미지원 언어 → `plain text` 자동 변환)
- GitHub PAT, Notion 토큰은 노출 시 즉시 로테이션 필요

---

## 🛠️ 유지보수 기록

### 2026-03-25: 초기 구축
- Claude Desktop에서 스크립트 작성 + GitHub Actions 워크플로우 생성
- 10개 카테고리 초기 데이터 Notion에 수동 추가
- GitHub Secrets 등록 (ANTHROPIC_API_KEY, NOTION_API_KEY, NOTION_DATABASE_ID)

### 2026-03-25: 콘텐츠 품질 개선
- 1단계 → 3단계 분리 생성 방식 전환 (웹검색 → 메타데이터 → 본문)
- 본문 프롬프트를 이전 잘 만든 페이지 형식 기반으로 재설계
- Notion 블록 변환 강화 (네이티브 테이블, 코드블록, 콜아웃)
- Notion 코드블록 미지원 언어 검증 추가 (ini → plain text 등)

### 2026-03-25: Rate limit 대응
- 카테고리 간 90초 대기 추가
- 실패 시 120초/240초 재시도 로직 (최대 3회)

### 2026-03-25: --force, --per-version 옵션 추가
- `--force`: 중복 체크 무시 (전체 재생성 시 사용)
- `--per-version`: UE 버전별 개별 페이지 생성

### 2026-03-26: 🆕 신규 정보 표기 시스템
- Notion DB에 `🆕 신규` 체크박스 속성 추가
- 오늘 생성 페이지: 제목 `🆕` + 체크박스 ON
- 다음날 실행 시: 어제 이전 페이지 `🆕` 제거 + 체크박스 OFF
- 본문 내 최근 1주 새 정보에 🆕 이모지 표기 요청

### 2026-04-11: 병행 브리핑 전략 도입 & 비용 최적화

#### 비용 최적화: STEP 2 Haiku 전환
- STEP 2 (메타데이터 추출)의 모델을 `claude-sonnet-4-6` → `claude-haiku-4-5-20251001`로 변경
- STEP 1 (웹검색), STEP 3 (본문 생성)은 Sonnet 유지
- 예상 비용 절감: ~30%
- 패치 가이드: `briefing-py-haiku-patch.md` 참조

#### 병행 브리핑 체계

| 방식 | 용도 | 비용 | 자동화 | 출력 |
|------|------|------|--------|------|
| **briefing.py** (자동) | 일일 모니터링 (10개 카테고리) | Anthropic API 종량제 | GitHub Actions 매일 9시 | Notion DB |
| **Claude Code `/briefing`** (수동) | 심화 분석, 주간/월간 종합 리포트 | Max 플랜 내 포함 ($0) | 수동 요청 | `Briefing/` 폴더 .md |

#### Claude Code `/브리핑` 명령어
- 위치: `.claude/commands/브리핑.md`
- 6개 카테고리 병렬 웹서치: 공식 채널, 커뮤니티, 업계 뉴스, GitHub, 핵심 키워드, 교육/심화
- 이전 브리핑 대비 신규 정보 비교 & 🆕 표기
- 특정 주제 심화 모드 지원 (예: `/briefing AnimNext`)
- 기존 `Briefing/YYYY-MM-DD/` 폴더 구조 유지
