# UE 분석 정확도 규칙

UE 에셋/노드/API에 대한 답변 품질을 높이기 위한 자기 검증 규칙.
답변 전에 이 체크리스트를 따르고, 확신이 없으면 추측 대신 검증 단계로 이동한다.

## 0. 절차 강도 = 문제 난이도 (제일 먼저 판정)

모든 항목을 매번 다 돌리지 않는다. 난이도에 비례해 절차를 켠다 — 단순 질문에 풀 검수를 거는 것이 정확도를 높이지 않고 토큰·지연만 늘린다.

- **Tier 0 — 단순 조회·사실 확인** ("이 값 뭐야", "기본값/시그니처 알려줘"): grounding(캐시/dump/메모리) 후 **즉답**. 후보 3개·reviewer·Hermes 블록 **생성 안 함**. §2(버전)·§3(출처)만 지킨다.
- **Tier 1 — 가역 진단·튜닝** ("왜 이렇게 동작", "값 바꿔줘"): inspector 실측 + 원인 정리. 후보는 필요한 만큼(억지로 3개 채우지 않음). reviewer/Hermes는 **선택**.
- **Tier 2 — 비가역·고위험** (에셋 그래프 변경, P4 영향, 반복 실패한 문제): 풀 검수 — 후보 다각화·단일변수·reviewer·`/evidence`. 여기서만 §10 핸드오프가 기본.

판정이 애매하면 **한 단계 낮게 시작**하고, 위험 신호(비가역 변경, 과거 실패 처방, ground truth 충돌)가 보이면 그때 올린다.

## 1. 답변 전 Verification

노드/에셋/파라미터 관련 질문엔 **추측 전에 팩트 체크**:

1. **에셋 경로/내용이 필요**: `scripts/analyze_*.py` 패턴으로 Python 스크립트 작성 → 사용자에게 실행 요청 → 결과 기반 답변
2. **API/노드 시그니처가 필요**: UnrealClaude MCP (localhost:3000) 또는 UE 소스 조회 (`gh api /repos/EpicGames/UnrealEngine/contents/...`) 시도
3. **바이너리 에셋 내용이 필요**: `tr -c '[:print:]\n' '\n' < xxx.uasset | grep` 로 printable string 추출

## 2. 버전 명시 의무

UE 관련 주장엔 **버전 태그 필수**:
- `UE 5.6` / `UE 5.7` / `UE 5.7.4`
- `GASP` (Game Animation Sample, Epic 공식)
- `SB2 custom` (회사 커스텀 빌드)
- `AnimNext / UAF` (신규 시스템) vs `ABP` (레거시)

버전별 차이 예: `AnimGraphNode_FootPlacement`는 UE 5.3+ 신규, 이전 버전엔 `LegIK`만.

## 3. 출처 표기

중요한 기술 주장엔 출처 하나 이상:
- Epic docs URL (`docs.unrealengine.com/...`)
- UE 소스 경로+라인 (`Engine/Plugins/Animation/.../AnimNode_FootPlacement.cpp:123`)
- 커뮤니티 분석 (Zhihu, Qiita, CEDEC 슬라이드 등)
- 메모리 파일 참조 (`reference_foot_placement_gasp.md`)

**금지**: "일반적으로", "보통은" 같은 모호한 근거로 구체 수치 제시.

## 4. 파라미터 값 추정 금지

"강성 120, 감쇠 22 권장" 같은 구체 숫자는:
- ✅ 공식 문서/샘플 값 인용 시 OK
- ✅ 물리 공식(critical damping 등) 유도 시 OK
- ❌ "경험상" 또는 "대략" 기반이면 **추정임을 명시**

현재 프로젝트 값 확인이 가능하면 **확인 후 조언**:
```
사용자: "값 얼마로 할까?"
나: "현재 값 먼저 확인할게" → analyze 스크립트 → "현재 X니까 Y로 변경 권장"
```

## 5. Output Log / 실측 데이터 우선

문제 진단 시:
- 추측으로 원인 나열하지 말고 **Log / Show Debug / PIE 관찰 결과 요청 먼저**
- 로그 파일 위치: `{Project}/Saved/Logs/{Project}.log`
- 유용한 콘솔 명령: `ShowDebug Character`, `show Collision`, `stat anim`
- 크래시: Callstack에서 `UnrealEditor-*.dll` 프레임 확인

## 6. "모름"을 잘못된 확신보다 선호

불확실한 영역:
- UAF/AnimNext 내부 API (문서 미완, UE 5.7도 preview 단계 잔존)
- UE 5.7 신규 기능의 구현 세부
- 커스텀 엔진 (SB2) 특이 동작

이 영역엔:
- "확실하진 않지만..." 명시
- 사용자 직접 확인 방법 제시 (에디터 열고 X 클릭 → Y 보기)
- 또는 UE 소스 조회/문서 조회로 검증

## 7. 한국어 UE 필드명 매핑

SB2 빌드는 한글화 설정 가능. 필드명을 영문으로만 부르면 못 찾을 수 있음.
주요 매핑을 `reference_foot_placement_gasp.md` 등 메모리에 축적.

예:
- 선형 강성 = Linear Stiffness
- 가로 리밸런싱 가중치 = Horizontal Rebalancing Weight
- 골반높이 모드 = Pelvis Height Mode

## 8. 반례/제약 명시

권장 파라미터에 **작동 안 하는 조건** 같이 적기:
- "값 X 권장. 단 Motion Matching 없으면 효과 없음"
- "오르막 유리. 내리막에선 반대 효과 — 부분 대응만 가능"

## 9. 메모리 업데이트 의무

검증된 새 사실은 메모리에:
- 확인된 에셋 경로/구조 → `project_*.md`
- 공식 동작/API → `reference_*.md`
- 사용자 선호/판단 → `user_*.md` 또는 `feedback_*.md`

특히 **사용자가 내 가설을 반박하면** (예: "GASP는 둘 다 쓰는데?"), 피드백 메모리로 기록.

## 10. 검증 핸드오프는 /evidence 로 위임 (자동 상시 출력 금지)

Hermes(비동기 반박·검수자) 검증 요청 블록은 **단일 출처인 `/evidence` 커맨드에서만** 생성한다. 묻지도 않았는데 자동으로 출력하지 않는다. 생성 여부는 §0 Tier 로 판정:
- **Tier 0~1**: 자동 출력 안 함. 사용자가 `/evidence` 를 호출하거나 명시 요청할 때만.
- **Tier 2** (비가역 에셋 변경 / 반복 실패 문제): 적용 직전 `/evidence` 패킷 + Hermes 블록 생성 권장.

(왕복 자동화는 Hermes 호스트 제약으로 불가 → 복붙 마찰 최소화가 차선)

**검증 타이밍** = 다음 중 하나:
- 원인 후보를 좁혀 결론에 도달 (에셋 수정 적용 **직전**)
- Tuner 변경 후 PIE 검증 직전/직후
- 가설을 채택/기각 판정하는 시점

블록 형식은 **`commands/evidence.md` 의 "Hermes 교차검증 핸드오프" 절을 단일 출처로 따른다** (여기 중복 정의하지 않음 — drift 방지).

원칙:
- **Hermes 응답은 ground truth 아님** → 실측 재확인 후 반영 (메모리 [[reference-hermes-reviewer-role]])
- Tier 0~1 은 생략이 기본. Tier 2 라도 후보 1개로 자명하면 생략 가능.
- 회사 코드/토큰 대량 덤프 금지, 판단 근거 값만 압축
- **검수 결과 기록**: Hermes 지적을 실측 판정한 뒤 [[reference-hermes-review-outcomes]] 에 1줄(적중/오류/부분 + 교훈) 추가 → Hermes auto-learn 캘리브레이션

## 11. 메모리 신뢰도 태깅

새 메모리/인덱스 항목(특히 수치·원인 주장)엔 검증 상태 태그를 단다. 표준: 메모리 [[reference-memory-status-tags]].
- `✅ 실측 YYYY-MM-DD` (Monolith/PIE/로그 검증) / `⚠ 가설`·`⚠ 미적용` (미검증) / `📄 외부` (docs·소스) / `❌ 폐기`(→대체 명시)
- 목적: Hermes·미래 세션이 가설을 사실로 오인하는 것 방지. `✅`도 날짜 오래되면 실측 재확인.
- 처방을 "미적용"으로 남길 땐 반드시 `⚠ 미적용` 명시 (적용된 줄 오인 방지).
