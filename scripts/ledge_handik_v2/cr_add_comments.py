# CR 코멘트 박스 생성 (2026-07-21) — 클러스터별 문서화
# 노드 실측 좌표(cr_snapshot) 기반으로 7개 영역을 감싼다. add_comment_node 는 코스메틱이라 안전.
import unreal, json

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/cr_comments.json"
CR = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_CtrlRig_LedgeDangle"

# (이름, x, y, w, h, r, g, b, 내용)
BOXES = [
    ("Cmt_PelvisSpring", -3560, -560, 2600, 1200, 0.35, 0.30, 0.10,
     "펠비스 스프링 v12 (가산 구조)\n"
     "Target = 펠비스 그대로 (속도항 제거). offset = (Spring - P) x 비율(X0 / Y0.9 / Z0.5) x 커브게이트 -> Clamp(45) 후 가산.\n"
     "강성 3.0 / 감쇠 0.25 — 스프링 체감은 감쇠로 확보 (진폭이 아니라 튕김).\n"
     "커브(ledge_pelvis_spring)는 ABP가 CharVelocity 핀에 (c,c,c)로 실어보냄 (속도 경로 재활용)."),

    ("Cmt_HandL", -820, -540, 2100, 940, 0.10, 0.25, 0.40,
     "왼손 핸드IK — 타깃 Lerp + 신전클램프 + TwoBoneIK\n"
     "Lerp(애님손-어깨보정, W2RL(HandTargetL), HandPinAlphaL) -> 신전클램프(어깨 기준) -> TwoBoneIK(폴=팔꿈치+바이어스)\n"
     "!! 7/21 오삭제 복구 구간: RestoreHandLerpL.T = 0 (왼손 IK OFF 대기 상태)\n"
     "   원복 = Get HandPinAlphaL -> RestoreHandLerpL.T / Get HandTargetL -> W2RL.Value 연결"),

    ("Cmt_HandR", 1320, -540, 2100, 1180, 0.10, 0.25, 0.40,
     "오른손 핸드IK — 왼손과 동일 구조\n"
     "Lerp(애님손-어깨보정, W2RR(HandTargetR), HandPinAlphaR) -> 신전클램프(ReachShoulderR 기준) -> TwoBoneIK(폴=팔꿈치+바이어스)"),

    ("Cmt_AnkleCapture", 3780, -560, 1260, 700, 0.40, 0.15, 0.30,
     "발목 로컬 캡처 (발 IK 전, 7/21)\n"
     "Rel = Inv(calf 글로벌) x foot 글로벌 -> Set AnkleRelL/R\n"
     "발 IK가 calf를 돌려도 발목 각도를 애님 그대로 보존하기 위한 사전 캡처.\n"
     "pure 노드는 소비 시점에 평가되므로 IK '전' 값을 변수에 담아둬야 한다."),

    ("Cmt_FootIK1", 5090, -560, 3360, 1060, 0.12, 0.35, 0.15,
     "발 IK 1패스 L/R (벽짚기)\n"
     "타깃 = ToeConv = FootTarget - (ball - foot)애님   <- FootTarget은 'ball'이 도달할 지점\n"
     "Lerp(애님 foot, 타깃, FootAlpha) -> 신전클램프 76 (thigh 기준) -> TwoBoneIK (폴=무릎+바이어스, propagate)"),

    ("Cmt_AnkleApply", 8560, -560, 1560, 640, 0.40, 0.15, 0.30,
     "발목 회전 보존 적용 (1패스 후)\n"
     "foot 회전 = calf(IK 후 글로벌) x AnkleRel -> SetRotation(Global, propagate)\n"
     "실측: 알파 1 구간 발목 편차 65도 -> 0.9도. 알파 0이면 항등(애님 그대로) = 안전."),

    ("Cmt_FootIK2", 10120, -560, 4480, 1160, 0.30, 0.20, 0.40,
     "발 IK 2패스 (7/21) — 발목 보존과 ball 접지 동시 해결\n"
     "회전 보존을 켜면 ToeConv(애님 회전 기준)와 어긋나 ball이 ~5cm 밀린다 -> 1패스 후 '실제' ball을 재측정,\n"
     "err = FootTarget - ball 만큼 이펙터 보정 -> 재IK -> 발목 회전 재보존. 오차 5cm -> 0.2cm 수준 1회 수렴.\n"
     "Weight는 GetFootAlpha 공유 (알파 0 = 전체 패스스루)."),
]

log = {"created": [], "errors": []}
try:
    bp = unreal.load_asset(CR)
    c = bp.get_controller_by_name("RigVMModel") or bp.get_controller()
    for name, x, y, w, h, r, g, b, text in BOXES:
        try:
            n = c.add_comment_node(text, unreal.Vector2D(x, y), unreal.Vector2D(w, h),
                                   unreal.LinearColor(r, g, b, 1.0), name)
            log["created"].append(str(n.get_node_path()) if n else "None:" + name)
        except Exception as e:
            log["errors"].append({name: repr(e)[:150]})
    bp.recompile_vm()
    log["saved"] = bool(unreal.EditorAssetLibrary.save_asset(CR, only_if_is_dirty=False))
except Exception:
    import traceback
    log["error"] = traceback.format_exc()

with open(OUT, "w") as fp:
    json.dump(log, fp, indent=1, ensure_ascii=False)
print("CR_COMMENTS created=%d err=%d" % (len(log["created"]), len(log["errors"])))
