# -*- coding: utf-8 -*-
"""
WallHandIK 저장본 상태 검증 (read-only) — 2026-06-29
====================================================
6/26 최종 설정(wallhand_config_20260626.py 의 target 값)과
디스크 로드된 CR 의 실제 핀값을 대조해 일치/불일치를 판정한다.

목적: CR 이 미저장 churn 으로 디스크 옛버전으로 롤백됐는지 실측 확인.
      불일치가 나오면 = 저장 안 됨 → wallhand_config_20260626.py 재적용+저장 필요.

쓰기/컴파일/저장 전혀 안 함. 순수 read.

에디터 Python 콘솔 또는 Monolith editor_query("run_console_command", "py <path>") 에서 실행.
출력 파일을 Read 로 회수.
"""
import unreal, traceback

CR = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
OUT = r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\f525ae6b-fccb-4356-b678-43eef9ec8640\scratchpad\wallhand_saved_state.txt"

# (pin, expected) — 6/26 최종값. float 은 문자열 비교 대신 근사 비교.
EXPECTED = [
    ("PalmAim.Primary.Kind", "Direction"),
    ("PalmAim_1.Primary.Kind", "Direction"),
    ("SecAxisLerp_2.A.X", "0.0"), ("SecAxisLerp_2.A.Y", "1.0"), ("SecAxisLerp_2.A.Z", "0.0"),
    ("SecAxisLerp_2.B.X", "-1.0"), ("SecAxisLerp_2.B.Y", "0.0"), ("SecAxisLerp_2.B.Z", "0.0"),
    ("SecAxisLerp_3.A.X", "0.0"), ("SecAxisLerp_3.A.Y", "-1.0"), ("SecAxisLerp_3.A.Z", "0.0"),
    ("SecAxisLerp_3.B.X", "1.0"), ("SecAxisLerp_3.B.Y", "0.0"), ("SecAxisLerp_3.B.Z", "0.0"),
    ("PalmAim.Secondary.Kind", "Location"),
    ("PalmAim_1.Secondary.Kind", "Location"),
    ("PalmAim.Secondary.Weight", "1.0"),
    ("PalmAim_1.Secondary.Weight", "1.0"),
    ("SecAxisLerp.A.X", "1.0"), ("SecAxisLerp.A.Y", "0.0"), ("SecAxisLerp.A.Z", "0.0"),
    ("SecAxisLerp.B.X", "0.0"), ("SecAxisLerp.B.Y", "1.0"), ("SecAxisLerp.B.Z", "0.0"),
    ("SecAxisLerp_1.A.X", "-1.0"), ("SecAxisLerp_1.A.Y", "0.0"), ("SecAxisLerp_1.A.Z", "0.0"),
    ("SecAxisLerp_1.B.X", "0.0"), ("SecAxisLerp_1.B.Y", "-1.0"), ("SecAxisLerp_1.B.Z", "0.0"),
    ("ReachBlend.SourceMinimum", "40.0"), ("ReachBlend.SourceMaximum", "60.0"),
    ("ReachBlend.TargetMinimum", "0.0"), ("ReachBlend.TargetMaximum", "1.0"),
    ("ReachBlend.bClamp", "true"),
    ("TwoBoneIK_R.PoleVector.X", "-1.0"), ("TwoBoneIK_R.PoleVector.Y", "0.0"), ("TwoBoneIK_R.PoleVector.Z", "-1.0"),
    ("TwoBoneIK_L.PoleVector.X", "1.0"), ("TwoBoneIK_L.PoleVector.Y", "0.0"), ("TwoBoneIK_L.PoleVector.Z", "-1.0"),
    ("MulK.B", "0.5"),
    ("Mul_spine_02.B", "0.4"), ("Mul_spine_03.B", "0.8"),
    ("Mul_neck_02.B", "-0.5"), ("Mul_head.B", "-0.7"),
    ("Off_spine_02.Weight", "1.0"), ("Off_spine_03.Weight", "1.0"),
    ("Off_neck_02.Weight", "1.0"), ("Off_head.Weight", "1.0"),
]

lines = []
def w(s): lines.append(str(s))

def approx_eq(actual, expected):
    a = str(actual).strip()
    e = str(expected).strip()
    if a == e:
        return True
    try:
        return abs(float(a) - float(e)) < 1e-4
    except (ValueError, TypeError):
        return a.lower() == e.lower()

try:
    bp = unreal.load_asset(CR)
    ctrl = bp.get_controller_by_name("RigVMModel")
    g = ctrl.get_graph()
    node_paths = set()
    for n in g.get_nodes():
        node_paths.add(n.get_node_path())
    w("=== nodes present ===")
    w("  " + ", ".join(sorted(node_paths)))

    # pin 값 조회: 노드별 pin path 로 default 값 읽기
    def get_pin_val(pinpath):
        node_name = pinpath.split(".")[0]
        target = None
        for n in g.get_nodes():
            if n.get_node_path() == node_name:
                target = n
                break
        if target is None:
            return "<NODE MISSING>"
        # sub-pin 탐색
        wanted = pinpath
        for p in target.get_pins():
            if p.get_pin_path() == wanted:
                return p.get_default_value()
            for sp in p.get_sub_pins():
                if sp.get_pin_path() == wanted:
                    return sp.get_default_value()
                for ssp in sp.get_sub_pins():
                    if ssp.get_pin_path() == wanted:
                        return ssp.get_default_value()
        return "<PIN MISSING>"

    w("\n=== diff vs 6/26 final ===")
    mism = 0
    miss = 0
    for pin, exp in EXPECTED:
        act = get_pin_val(pin)
        if "MISSING" in str(act):
            miss += 1
            w(f"  [MISSING] {pin}  expected={exp}  got={act}")
        elif approx_eq(act, exp):
            w(f"  [ OK ] {pin} = {act}")
        else:
            mism += 1
            w(f"  [MISMATCH] {pin}  expected={exp}  got={act!r}")

    w("\n=== SUMMARY ===")
    w(f"  total={len(EXPECTED)}  ok={len(EXPECTED)-mism-miss}  mismatch={mism}  missing={miss}")
    if mism == 0 and miss == 0:
        w("  VERDICT: SAVED STATE MATCHES 6/26 FINAL (no churn rollback)")
    elif miss > 0:
        w("  VERDICT: NODES/PINS MISSING — graph topology differs (churn or restructure)")
    else:
        w("  VERDICT: VALUES DRIFTED — re-apply wallhand_config_20260626.py + save")
except Exception:
    w("\n!!! EXC:\n" + traceback.format_exc())

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
unreal.log("[wallhand_saved_state] done -> " + OUT)
print("\n".join(lines))
