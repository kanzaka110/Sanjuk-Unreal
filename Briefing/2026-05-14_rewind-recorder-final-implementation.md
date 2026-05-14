# 2026-05-14 — AnimRewindRecorder 최종 구현 (66필드 단일 FT) + 재구현 가이드

## 최종 상태 한 줄 요약

PC_01 ABP `AnimRewindRecorderEmit` 그래프 안에 **`K2Node_FormatText_2` 단일 거대 노드**가 매 틱 `[ANIM_REC]` 로그 라인을 emit. 66필드를 받아 한 줄로 포맷. 옛 8개 FT chain은 모두 삭제됨.

---

## 핵심 구조 (5/14 최종)

### 노드 토폴로지

```
[65 source nodes] ──wires──→ K2Node_FormatText_2 ──Result──┬──→ K2Node_CallFunction_4.InText   (UE_LOG 출력)
                                                            └──→ K2Node_VariableSet_1.RewindMonitorLine (변수 저장)
```

- **단일 FormatText:** `K2Node_FormatText_2` (66 input arg pins + 1 Format pin)
- **삭제됨:** `K2Node_FormatText_8, _4, _0, _5, _11, _13, _12, _1` (옛 chain)
- **vac 핀만 default `"-1"`** (Array_Length wire 없이)
- **나머지 65 wire** — 아래 매핑 그대로

### 자산 메타

```
ASSET     = /Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP
GRAPH     = AnimRewindRecorderEmit
ENDPOINT  = http://localhost:9316/mcp
NEW_FT_ID = K2Node_FormatText_2
NEW_FT_POS = [7280, 1500]
```

### 66필드 Format 문자열

```
[ANIM_REC] "f"={f},"sp"={sp},"as"={as},"ms"={ms},"ist"={ist},"he"={he},
"vlen"={vlen},"pwm"={pwm},"il"={il},"isf"={isf},"isc"={isc},"csh"={csh},
"trd"={trd},"ib"={ib},"rmf"={rmf},"fik"={fik},"fca"={fca},"ow"={ow},
"ig"={ig},"sc"={sc},"clip"={clip},"seq"={seq},"bim"={bim},"bpim"={bpim},
"ms_l"={ms_l},"ms_p"={ms_p},"mm"={mm},"ops"={ops},"fbsw"={fbsw},"fa"={fa},
"rop"={rop},"sba"={sba},"ibk"={ibk},"we"={we},"iw"={iw},"jes"={jes},
"htt"={htt},"stip"={stip},"ip"={ip},"lm"={lm},"dal"={dal},"sset"={sset},
"phase"={phase},"eow"={eow},"eprw"={eprw},"fv"={fv},"acc"={acc},
"isafb"={isafb},"isaub"={isaub},"sswseq"={sswseq},"wt"={wt},"cvco"={cvco},
"ubsw"={ubsw},"rva"={rva},"rvmci"={rvmci},"ifl"={ifl},"rj"={rj},"dog"={dog},
"hd"={hd},"pav_z"={pav_z},"cav_z"={cav_z},"sms"={sms},"vac"={vac},
"na"={na},"rrt"={rrt},"rrr"={rrr}
```

총 66 필드. 정확히 `scripts/consolidate_ft_chain_step1.py:30-43` 의 `FORMAT_STR`.

### 65 wire 매핑 (vac 제외)

| dest_pin | src_node | src_pin |
|----------|----------|---------|
| f | K2Node_CallFunction_3 | ReturnValue |
| sp | K2Node_VariableGet_2 | Speed2D |
| as | K2Node_CallFunction_7 | ReturnValue |
| ms | K2Node_CallFunction_8 | ReturnValue |
| ist | K2Node_VariableGet_5 | bIsStart |
| he | K2Node_VariableGet_6 | HasEvade |
| vlen | K2Node_CallFunction_13 | ReturnValue |
| pwm | K2Node_CallFunction_14 | ReturnValue |
| il | K2Node_VariableGet_10 | IsLockOn |
| isf | K2Node_VariableGet_32 | IsStrafe |
| isc | K2Node_VariableGet_33 | TrjIsCircling |
| csh | K2Node_VariableGet_34 | CircleStrafeHysteresis |
| trd | K2Node_VariableGet_14 | TargetRotationDelta |
| ib | K2Node_VariableGet_25 | IsBattle |
| rmf | K2Node_VariableGet_16 | RuleMoveFlag |
| fik | K2Node_VariableGet_35 | FootIKWeight |
| fca | K2Node_VariableGet_18 | FootClampAlpha |
| ow | K2Node_VariableGet_19 | OverlayWeight |
| ig | K2Node_VariableGet_36 | IsGuarding |
| sc | K2Node_VariableGet_7 | SearchCost |
| clip | K2Node_VariableGet_26 | CurrAnimTag |
| seq | K2Node_VariableGet_37 | CurrentSequenceName |
| bim | K2Node_VariableGet_39 | bIsMoving |
| bpim | K2Node_VariableGet_15 | bPrevIsMoving |
| ms_l | K2Node_CallFunction_0 | ReturnValue |
| ms_p | K2Node_CallFunction_1 | ReturnValue |
| mm | K2Node_GetEnumeratorNameAsString_6 | ReturnValue |
| ops | K2Node_GetEnumeratorNameAsString_3 | ReturnValue |
| fbsw | K2Node_VariableGet_28 | FullBodySlotWeight |
| fa | K2Node_VariableGet_29 | IsFullBodySlotActive |
| rop | K2Node_VariableGet_59 | ResetOffsetPulse |
| sba | K2Node_VariableGet_20 | IsSequenceBindingActor |
| ibk | K2Node_VariableGet_17 | IsBlocked |
| we | K2Node_VariableGet_43 | WriggleEnd |
| iw | K2Node_VariableGet_38 | InWriggle |
| jes | K2Node_VariableGet_11 | JustExitedSprint |
| htt | K2Node_VariableGet_56 | HoldTimeThreshold |
| stip | K2Node_CallFunction_9 | ReturnValue |
| ip | K2Node_CallFunction_52 | ReturnValue |
| lm | K2Node_CallFunction_118 | ReturnValue |
| dal | K2Node_CallFunction_121 | ReturnValue |
| sset | K2Node_VariableGet_41 | bIsSprintEndTransition |
| phase | K2Node_CallFunction_46 | ReturnValue |
| eow | K2Node_CallFunction_48 | ReturnValue |
| eprw | K2Node_CallFunction_18 | ReturnValue |
| fv | K2Node_CallFunction_119 | ReturnValue |
| acc | K2Node_CallFunction_120 | ReturnValue |
| isafb | K2Node_CallFunction_40 | ReturnValue |
| isaub | K2Node_CallFunction_16 | ReturnValue |
| sswseq | K2Node_CallFunction_44 | ReturnValue |
| wt | K2Node_GetEnumeratorNameAsString_7 | ReturnValue |
| cvco | K2Node_CallFunction_11 | ReturnValue |
| ubsw | K2Node_VariableGet_30 | UpperBodyBlendWeight |
| rva | K2Node_GetEnumeratorNameAsString_5 | ReturnValue |
| rvmci | K2Node_CallFunction_43 | ReturnValue_MatchedConfigIndex |
| ifl | K2Node_CallFunction_43 | ReturnValue_bIsFalling |
| rj | K2Node_CallFunction_43 | ReturnValue_bRequiresJump |
| dog | K2Node_CallFunction_43 | ReturnValue_DiffOnGround |
| hd | K2Node_CallFunction_43 | ReturnValue_HeightDiff |
| pav_z | K2Node_VariableGet_46 | TrjPastAngularVelocity_Z |
| cav_z | K2Node_VariableGet_13 | TrjCurrentAngularVelocity_Z |
| sms | K2Node_CallFunction_6 | ReturnValue |
| na | K2Node_VariableGet_42 | NullAnim |
| rrt | K2Node_VariableGet_44 | RunRetransit |
| rrr | K2Node_VariableGet_45 | RetransitReason |
| **vac** | — DEFAULT `"-1"` | (와이어 없음) |

**전체 출처:** `scripts/consolidate_ft_chain_step2.py:31-98` 의 `WIRES` 튜플 — 그대로 사용 가능

---

## 재구현 단계 (clean state에서 step1→step6)

원본 8개 FT chain이 살아있다면 step1→step6 순서 그대로. 옛 chain이 없는 clean state에서는 step1+step2만 돌리고 step4의 downstream 와이어를 직접 추가하면 됨 (step3/5/6 불필요).

### Phase 1: 새 FT 생성 + 핀 자동 생성
```
scripts/consolidate_ft_chain_step1.py
```
- `add_node`로 `format_text` 타입 추가
- `format` extra에 FORMAT_STR 전달 → 66 input pin 자동 생성
- 위치: `[7280, 1500]`
- 결과: `K2Node_FormatText_2` 생성 확인 → `dump_new_ft_pins.py`로 검증

### Phase 2: 65 wire 연결
```
scripts/consolidate_ft_chain_step2.py
```
- WIRES 튜플 65개 순차 `connect_pins`
- vac 핀에 `set_pin_default("-1")`
- 실패 wire 리스트업 + 종료코드 2

### Phase 3 (인라인): compile
```
compile_blueprint 호출만
```

### Phase 4: downstream 스왑
```
scripts/consolidate_ft_chain_step4.py
```
- `K2Node_FormatText_1.Result` 끊기:
  - → `K2Node_CallFunction_4.InText`
  - → `K2Node_VariableSet_1.RewindMonitorLine`
- `K2Node_FormatText_2.Result` 연결 (위와 동일 target 2곳)

> **Clean state에서는** `FT_1`이 없으므로 disconnect는 skip, connect만 실행

### Phase 5 (인라인): compile + verify
```
inspect_ft_routing.py
```
- FT_2.Result → CF_4.InText / VarSet_1.RewindMonitorLine 연결 확인

### Phase 6: 옛 8개 FT 삭제 + compile
```
scripts/consolidate_ft_chain_step6.py
```
- `K2Node_FormatText_8, _4, _0, _5, _11, _13, _12, _1` 순서로 `remove_node`
- 각 삭제 후 `compile_blueprint` → error_count > 0 이면 abort

> **Clean state에서는** 이미 없으므로 skip

---

## 내일 빠른 재구현 의사결정 트리

### Step 0: 진단 (PIE 안 켜고도 가능)

```
py C:/Dev/Sanjuk-Unreal/scripts/dump_consolidated_graph.py
py C:/Dev/Sanjuk-Unreal/scripts/dump_new_ft_pins.py
py C:/Dev/Sanjuk-Unreal/scripts/inspect_ft_routing.py
```

결과로 다음 4가지 확인:

| 항목 | 정상 상태 |
|------|----------|
| `K2Node_FormatText_2` 존재 | O |
| FT_2 input arg pins 개수 | 66 (Format 핀 제외) |
| 65 wire 연결 | 모두 connected |
| FT_2.Result → CF_4.InText + VarSet_1.RewindMonitorLine | 둘 다 |

### 시나리오별 처방

| 진단 결과 | 시나리오 | 실행 |
|-----------|---------|------|
| 모두 정상 | F. 정상 | 아무것도 안 함 |
| FT_2 없음 + 옛 FT chain 살아있음 | B1 | step1 → step2 → compile → step4 → compile → step6 |
| FT_2 없음 + clean state | B2 | step1 → step2 → compile → connect FT_2.Result to downstream (step4 connect만) → compile |
| FT_2 있음, 핀 < 66 | 이상 케이스 | FT_2 삭제 후 B2 |
| FT_2 있음, 핀 66, wire < 65 | C | step2 (실패 wire만 재연결 — 별도 idempotent 스크립트 필요) |
| FT_2 있음, wire 65, downstream X | D | step4 (clean state 분기) |
| 다 있는데 옛 FT 살아남음 | E | step6 |
| 그래프 자체 없음 | A | **SB2 Saved/Autosaves/ 먼저 확인 — 백업 없이는 큰 작업** |

---

## 내일 첫 명령 (사용자가 "리와인드 로그 재구현" 요청 시)

1. **로컬 PC에서:**
   ```
   /pull
   ```
2. **진단 3종 실행 (UE Editor Python Console):**
   ```
   py C:/Dev/Sanjuk-Unreal/scripts/dump_consolidated_graph.py
   py C:/Dev/Sanjuk-Unreal/scripts/dump_new_ft_pins.py
   py C:/Dev/Sanjuk-Unreal/scripts/inspect_ft_routing.py
   ```
   → 결과 로그 공유
3. **시나리오 식별 후 위 표대로 실행**

> 가장 흔할 시나리오는 B2 (clean state) 또는 D (downstream 끊김). B2는 step1 + step2만 돌리고 step4의 connect 2개 추가 — **5분이면 끝남**.

---

## 보조: AnimRewindRecorder 외부 viewer

ABP 노드 복원 후 로그가 SB2_2.log에 다시 흐르면, viewer는 그대로 동작:

```
python scripts/anim_rec_viewer.py
# 또는 다른 로그 위치:
python scripts/anim_rec_viewer.py --log "E:/Perforce/SB2/Workspace/Internal/SB2/Saved/Logs/SB2.log"
```

> viewer 자체는 5/13에 23필드용으로 작성됨. 66필드 모두 표시되려면 `FIELD_LABELS` 딕셔너리를 확장해야 함 (5/14에 안 했을 수 있음 — 내일 확인 필요)

---

## 환경 제약

- Monolith API는 **로컬 PC localhost:9316** 에서만 접근 가능 → 재구현 작업은 로컬에서만
- GCP에서는 스크립트 검증 + 문서 작업만
