# 렛지 IK 레이어 펌프 진단 (2026-07-22 재구축 검증)
# 목적: ABP 계산값 vs IK레이어 복사값 프레임 대조 → 고장 지점 3분류 (계산/펌프/소비)
# 실행: 에디터 콘솔에서  py "H:/내 드라이브/Claude/Sanjuk-Unreal/scripts/ledge_handik_v2/probe_layer_pump.py"
# 해제: 같은 스크립트 재실행 시 기존 콜백 자동 해제 후 재설치
import unreal
import sys
import time
import types

for name in ("__ikv2__", "__ikdrift__", "__ikiso__", "__atprobe__", "__hover__",
             "__bodyp__", "__over__", "__slide__", "__pump__"):
    m = sys.modules.get(name)
    if m is not None and getattr(m, "handle", None) is not None:
        try:
            unreal.unregister_slate_post_tick_callback(m.handle)
        except Exception:
            pass
        m.handle = None

mod = types.ModuleType("__pump__")
sys.modules["__pump__"] = mod
LOG = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/pump.log"
open(LOG, "w").close()
NL = chr(10)
LAYER_CLASS_PATH = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK.PC_01_AnimLayer_IK_C"


def _v(o):
    return "(%.1f,%.1f,%.1f)" % (o.x, o.y, o.z)


def _tick(dt, _st={"last": 0.0}):
    try:
        now = time.time()
        if now - _st["last"] < 0.15:
            return
        _st["last"] = now
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
        cls = unreal.load_object(None, LAYER_CLASS_PATH)
        layer = mesh.get_linked_anim_layer_instance_by_class(cls) if cls else None
        lmd = abp.get_editor_property("LedgeMoveData")
        active = bool(lmd.get_editor_property("bActive"))
        lines = ["t=%.2f ledgeActive=%d" % (now, active)]
        # 1) ABP 계산값
        a_al = float(abp.get_editor_property("LedgeHandIKAlphaL"))
        a_ar = float(abp.get_editor_property("LedgeHandIKAlphaR"))
        a_pl = abp.get_editor_property("LedgeHandWorldPredL")
        a_da = float(abp.get_editor_property("LedgeDangleAlpha"))
        a_ph = float(abp.get_editor_property("LedgePhysAlpha"))
        a_fs = float(abp.get_editor_property("LedgeFootIKAlphaL"))
        lines.append("  ABP  alphaL=%.2f alphaR=%.2f dangle=%.2f phys=%.2f footL=%.2f predL=%s"
                     % (a_al, a_ar, a_da, a_ph, a_fs, _v(a_pl)))
        # 2) IK 레이어 복사값
        if layer is None:
            lines.append("  LAYER=None (linked instance 미발견!)")
        else:
            l_ref = layer.get_editor_property("As SBCharacter ABP")
            l_al = float(layer.get_editor_property("LedgeHandIKAlphaL"))
            l_ar = float(layer.get_editor_property("LedgeHandIKAlphaR"))
            l_pl = layer.get_editor_property("LedgeHandWorldPredL")
            l_da = float(layer.get_editor_property("LedgeDangleAlpha"))
            l_ph = float(layer.get_editor_property("LedgePhysAlpha"))
            l_fs = float(layer.get_editor_property("LedgeFootIKAlphaL"))
            lines.append("  LAYR alphaL=%.2f alphaR=%.2f dangle=%.2f phys=%.2f footL=%.2f predL=%s castRef=%s"
                         % (l_al, l_ar, l_da, l_ph, l_fs, _v(l_pl),
                            "OK" if l_ref else "NULL!"))
            d = max(abs(a_al - l_al), abs(a_ar - l_ar), abs(a_da - l_da))
            lines.append("  DIFF maxAlpha=%.3f predL_d=%.1f" % (
                d, (unreal.Vector(a_pl.x - l_pl.x, a_pl.y - l_pl.y, a_pl.z - l_pl.z)).length()))
        # 3) 적용 결과 대조: 실제 손 본 vs 타깃 vs 이중변환 가정점
        hand = mesh.get_socket_location("hand_l")
        ct = mesh.get_world_transform()
        dbl = ct.transform_location(a_pl)          # 월드 타깃을 한 번 더 컴포넌트 변환했다면
        inv = ct.inverse_transform_location(a_pl)  # 반대로 컴포넌트 좌표로 오해했다면
        err = (unreal.Vector(hand.x - a_pl.x, hand.y - a_pl.y, hand.z - a_pl.z)).length()
        err_dbl = (unreal.Vector(hand.x - dbl.x, hand.y - dbl.y, hand.z - dbl.z)).length()
        err_inv = (unreal.Vector(hand.x - inv.x, hand.y - inv.y, hand.z - inv.z)).length()
        lines.append("  APPLY handL=%s err(target)=%.1f err(doubleXform)=%.1f err(invXform)=%.1f alphaL=%.2f"
                     % (_v(hand), err, err_dbl, err_inv, a_al))
        with open(LOG, "a") as f:
            f.write(NL.join(lines) + NL)
    except Exception as e:
        with open(LOG, "a") as f:
            f.write("ERR " + repr(e)[:200] + NL)


mod.handle = unreal.register_slate_post_tick_callback(_tick)
unreal.log("[pump] probe installed -> " + LOG)
