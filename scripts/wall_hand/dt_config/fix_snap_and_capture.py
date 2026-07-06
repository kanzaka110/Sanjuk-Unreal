# -*- coding: utf-8 -*-
"""①fSelRel 중립화(릴리즈 weight-킬 제거 — 알파 커브가 단독 지휘)
②손 컴포넌트공간 쿼터니언 캡처 arm (PIE서 폰 감지되면 1회 기록)"""
import unreal, traceback

OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/fix_snap.txt"
CAP = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/hand_pose_capture.txt"
DST = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
L = []

def step(s):
    L.append(str(s))
    open(OUT, "w", encoding="utf-8").write("\n".join(L))

try:
    bp = unreal.load_asset(DST)
    ctrl = bp.get_controller_by_name("RigVMModel")
    for a, b in [("SelR.Result", "fSelRelR.IfTrue"), ("SelL.Result", "fSelRelL.IfTrue")]:
        try:
            ok = ctrl.add_link(a, b)
            step(f"{'lk' if ok else 'LKFALSE'} {a}->{b}")
        except Exception as e:
            step(f"LK ERR {a}->{b} {str(e)[:60]}")
except Exception:
    step("FATAL cr\n" + traceback.format_exc())

# ── 캡처 arm
state = {"done": False, "t": 0.0}

def tick(dt):
    if state["done"]:
        return
    state["t"] += dt
    if state["t"] < 0.5:
        return
    state["t"] = 0.0
    try:
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if not world:
            return
        pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
        if not pawn or "PC_01" not in pawn.get_name():
            return
        mesh = pawn.get_editor_property("Mesh")
        rows = []
        for b in ("hand_r", "hand_l"):
            tf = mesh.get_socket_transform(b, unreal.RelativeTransformSpace.RTS_COMPONENT)
            q = tf.rotation
            rows.append(f"{b}: (X={q.x:.6f},Y={q.y:.6f},Z={q.z:.6f},W={q.w:.6f})")
        open(CAP, "w", encoding="utf-8").write("\n".join(rows))
        state["done"] = True
    except Exception:
        open(CAP, "w", encoding="utf-8").write("CAPFAIL\n" + traceback.format_exc())
        state["done"] = True

h = unreal.register_slate_post_tick_callback(tick)
step(f"capture armed {h}")
