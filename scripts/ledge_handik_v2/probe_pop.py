# 렛지 IK 팝(튐) 캐처 (2026-07-22) — 매 슬레이트 틱 감시, 튀는 프레임만 전후 기록
# 판정: 프레임간 이동량이 문턱 초과하는 신호를 [TARGET-POP]/[BONE-POP]으로 분류
# 실행: 에디터 콘솔  py "H:/내 드라이브/Claude/Sanjuk-Unreal/scripts/ledge_handik_v2/probe_pop.py"
import unreal
import sys
import time
import types

for name in ("__ikv2__", "__ikdrift__", "__ikiso__", "__atprobe__", "__hover__",
             "__bodyp__", "__over__", "__slide__", "__pump__", "__pop__"):
    m = sys.modules.get(name)
    if m is not None and getattr(m, "handle", None) is not None:
        try:
            unreal.unregister_slate_post_tick_callback(m.handle)
        except Exception:
            pass
        m.handle = None

mod = types.ModuleType("__pop__")
sys.modules["__pop__"] = mod
LOG = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/pop.log"
open(LOG, "w").close()
NL = chr(10)
POP_CM = 12.0        # 프레임간 이동 문턱 (cm) — 정상 셔플 이동속도보다 크게
HIST = 4             # 팝 전 컨텍스트 프레임 수


def _v(o):
    return "(%.1f,%.1f,%.1f)" % (o.x, o.y, o.z)


def _d(a, b):
    return (unreal.Vector(a.x - b.x, a.y - b.y, a.z - b.z)).length()


def _tick(dt, _st={"prev": None, "hist": [], "npop": 0}):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None:
            return
        pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
        if pawn is None:
            return
        mesh = pawn.get_components_by_class(unreal.SkeletalMeshComponent)[0]
        abp = mesh.get_anim_instance()
        if abp is None:
            return
        lmd = abp.get_editor_property("LedgeMoveData")
        active = bool(lmd.get_editor_property("bActive"))
        # 비활성 구간도 기록 (진입/이탈 에지 관찰) — 비활성 5프레임 이후엔 스킵으로 볼륨 억제
        if not active:
            _st["inact"] = _st.get("inact", 0) + 1
            if _st["inact"] > 5 and _st.get("inact", 0) % 10 != 0:
                return
        else:
            _st["inact"] = 0
        ct = mesh.get_world_transform()
        cur = {
            "t": time.time(),
            "predL": abp.get_editor_property("LedgeHandWorldPredL"),
            "predR": abp.get_editor_property("LedgeHandWorldPredR"),
            "handL": mesh.get_socket_location("hand_l"),
            "handR": mesh.get_socket_location("hand_r"),
            "footL": mesh.get_socket_location("foot_l"),
            "footR": mesh.get_socket_location("foot_r"),
            "ftL": ct.transform_location(abp.get_editor_property("LedgeFootIdleCompL")),
            "ftR": ct.transform_location(abp.get_editor_property("LedgeFootIdleCompR")),
            "aL": float(abp.get_editor_property("LedgeHandIKAlphaL")),
            "aR": float(abp.get_editor_property("LedgeHandIKAlphaR")),
            "fL": float(abp.get_editor_property("LedgeFootIKAlphaL")),
            "fR": float(abp.get_editor_property("LedgeFootIKAlphaR")),
            "mvL": float(abp.get_curve_value("ledge_hand_move_l")),
            "mvR": float(abp.get_curve_value("ledge_hand_move_r")),
            "anchL": abp.get_editor_property("LedgeHandAnchorL"),
            "anchR": abp.get_editor_property("LedgeHandAnchorR"),
            "pelvis": mesh.get_socket_location("pelvis"),
            "spring": float(abp.get_editor_property("LedgePelvisSpring")),
            "dangle": float(abp.get_editor_property("LedgeDangleAlpha")),
            "mcL": float(abp.get_editor_property("LedgeMcBaseL")),
            "mcR": float(abp.get_editor_property("LedgeMcBaseR")),
            "umv": abp.get_editor_property("LedgeUnitMoveVec"),
            "td": float(abp.get_editor_property("LedgeDestTd")),
            "rel": bool(abp.get_editor_property("LedgeRelatch")),
            "bt": bool(lmd.get_editor_property("bTransitingToNextLedge")),
            "bum": bool(lmd.get_editor_property("bUnitMoveInProgress")),
            "ncc": lmd.get_editor_property("NextLedgeCandidateClosest"),
            "nca": float(lmd.get_editor_property("NextLedgeCandidateAlong")),
            "ncd": float(lmd.get_editor_property("NextLedgeCandidateDist")),
        }
        prev = _st["prev"]
        _st["prev"] = cur
        line = ("act=%d " % (1 if active else 0)) + ("t=%.3f aL=%.2f aR=%.2f fL=%.2f fR=%.2f mvL=%.2f mvR=%.2f dangle=%.2f spring=%.2f "
                "predL=%s predR=%s handL=%s handR=%s footL=%s footR=%s ftL=%s anchL=%s anchR=%s "
                "pelvis=%s relZ(hand-pelvis)=%.1f") % (
            cur["t"], cur["aL"], cur["aR"], cur["fL"], cur["fR"], cur["mvL"], cur["mvR"],
            cur["dangle"], cur["spring"],
            _v(cur["predL"]), _v(cur["predR"]), _v(cur["handL"]), _v(cur["handR"]),
            _v(cur["footL"]), _v(cur["footR"]), _v(cur["ftL"]), _v(cur["anchL"]), _v(cur["anchR"]),
            _v(cur["pelvis"]), cur["handL"].z - cur["pelvis"].z)
        line += " | mcL=%.2f mcR=%.2f umv=%s td=%.1f rel=%d" % (
            cur["mcL"], cur["mcR"], _v(cur["umv"]), cur["td"], cur["rel"])
        line += " | bt=%d bum=%d ncc=%s nca=%.1f ncd=%.1f" % (
            cur["bt"], cur["bum"], _v(cur["ncc"]), cur["nca"], cur["ncd"])
        _st["hist"].append(line)
        if len(_st["hist"]) > HIST:
            _st["hist"].pop(0)
        # 상시 하트비트 (0.3s) — 지속형 이상 자세도 잡히게
        if cur["t"] - _st.get("hb", 0.0) > 0.3:
            _st["hb"] = cur["t"]
            with open(LOG, "a") as f:
                f.write("HB " + line + NL)
        if prev is None:
            return
        pops = []
        for key, tag in (("predL", "TARGET-L"), ("predR", "TARGET-R"),
                         ("handL", "BONE-HL"), ("handR", "BONE-HR"),
                         ("footL", "BONE-FL"), ("footR", "BONE-FR"),
                         ("ftL", "FTGT-L"), ("ftR", "FTGT-R"),
                         ("anchL", "ANCH-L"), ("anchR", "ANCH-R")):
            dd = _d(cur[key], prev[key])
            if dd > POP_CM:
                pops.append("%s jump=%.1fcm %s->%s" % (tag, dd, _v(prev[key]), _v(cur[key])))
        if pops:
            _st["npop"] += 1
            with open(LOG, "a") as f:
                f.write("===== POP #%d =====%s" % (_st["npop"], NL))
                for h in _st["hist"][:-1]:
                    f.write("  ctx " + h + NL)
                f.write("  NOW " + line + NL)
                for p in pops:
                    f.write("  !! " + p + NL)
    except Exception as e:
        with open(LOG, "a") as f:
            f.write("ERR " + repr(e)[:200] + NL)


mod.handle = unreal.register_slate_post_tick_callback(_tick)
unreal.log("[pop] catcher installed -> " + LOG)
