"""v1 검증 증거 수집기 v2 (robust + self-diagnostic).
PIE 런타임: ABP WallHand* 4값 CSV + alpha 상승엣지 HighResShot.
실패해도 STATUS 파일에 매 틱 진단(world/pawn/abp/prop) 기록 → 원인 파악.
"""
import unreal, sys, time

CSV = r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\wallhand_pie_log.csv"
STATUS = r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\wallhand_pie_status.txt"
HKEY = "_WALLHAND_LOG_HANDLE"

try:
    old = getattr(sys, HKEY, None)
    if old is not None:
        unreal.unregister_slate_post_tick_callback(old)
except Exception:
    pass

with open(CSV, "w", encoding="utf-8") as f:
    f.write("t,speed,alphaTarget,alpha,tx,ty,tz,nx,ny,nz\n")

st = {"prev": 0.0, "last_shot": -99.0, "t0": None, "n": 0, "diag": 0}


def world_pie():
    # PIE 월드 찾기
    try:
        ws = unreal.EditorLevelLibrary.get_game_world()
        if ws is not None:
            return ws
    except Exception:
        pass
    try:
        sub = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        return sub.get_game_world()
    except Exception:
        return None


def find_pawn(world):
    try:
        p = unreal.GameplayStatics.get_player_pawn(world, 0)
        if p:
            return p, "player_pawn"
    except Exception:
        pass
    try:
        for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Pawn):
            if "PC_01_BP" in a.get_class().get_name():
                return a, "byclass"
    except Exception as e:
        return None, f"getall_err:{str(e)[:30]}"
    return None, "none"


def find_abp(pawn):
    mesh = None
    for getter in ("Mesh",):
        try:
            mesh = pawn.get_editor_property(getter)
            if mesh:
                break
        except Exception:
            mesh = None
    if mesh is None:
        try:
            mesh = pawn.get_component_by_class(unreal.SkeletalMeshComponent)
        except Exception:
            return None, "no_mesh"
    try:
        a = mesh.get_anim_instance()
        return a, (a.get_class().get_name() if a else "none")
    except Exception as e:
        return None, f"ai_err:{str(e)[:30]}"


def setstatus(s):
    try:
        with open(STATUS, "w", encoding="utf-8") as f:
            f.write(s)
    except Exception:
        pass


def tick(dt):
    try:
        w = world_pie()
        wt = (w.get_world_type() if w and hasattr(w, "get_world_type") else "?")
        if w is None:
            if st["n"] % 60 == 0:
                setstatus("world=None (PIE 아님?)")
            st["n"] += 1
            return
        pawn, pinfo = find_pawn(w)
        if pawn is None:
            if st["n"] % 60 == 0:
                setstatus(f"world ok type={wt} pawn=None ({pinfo})")
            st["n"] += 1
            return
        abp, ainfo = find_abp(pawn)
        if abp is None:
            if st["n"] % 60 == 0:
                setstatus(f"pawn ok={pawn.get_name()} abp=None ({ainfo})")
            st["n"] += 1
            return
        try:
            aT = float(abp.get_editor_property("WallHandAlphaTarget"))
            a = float(abp.get_editor_property("WallHandAlpha"))
            tgt = abp.get_editor_property("WallHandTargetWorld")
            nrm = abp.get_editor_property("WallHandNormal")
        except Exception as e:
            setstatus(f"abp ok={ainfo} PROP_ERR {str(e)[:60]}")
            st["n"] += 1
            return
        try:
            spd = float(pawn.get_velocity().size())
        except Exception:
            spd = -1.0
        now = unreal.GameplayStatics.get_time_seconds(w)
        if st["t0"] is None:
            st["t0"] = now
        t = now - st["t0"]
        with open(CSV, "a", encoding="utf-8") as f:
            f.write(f"{t:.3f},{spd:.1f},{aT:.3f},{a:.3f},{tgt.x:.1f},{tgt.y:.1f},{tgt.z:.1f},{nrm.x:.3f},{nrm.y:.3f},{nrm.z:.3f}\n")
        st["n"] += 1
        if st["n"] % 30 == 0:
            setstatus(f"LOGGING ok rows={st['n']} t={t:.1f} alpha={a:.2f} abp={ainfo}")
        # 자동 스크린샷 제거 (사용자 요청 — 벽 접촉 시 HighResShot 안 함)
        st["prev"] = a
    except Exception as e:
        setstatus(f"TICK_EXC {str(e)[:80]}")


h = unreal.register_slate_post_tick_callback(tick)
setattr(sys, HKEY, h)
setstatus("ARMED (idle until PIE)")
unreal.log(f"[wallhand_log v2] ARMED. CSV={CSV} STATUS={STATUS}")
