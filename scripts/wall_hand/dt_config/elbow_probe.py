# -*- coding: utf-8 -*-
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/elbow_probe.txt"
state = {"t": 0.0}
def tick(dt):
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
        rows = []
        # DA 값
        da = unreal.EditorAssetLibrary.load_asset("/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK/DA_WallHandIK")
        try:
            rows.append(f"DA.ElbowAngleDeg = {da.get_editor_property('ElbowAngleDeg')}")
        except Exception as e:
            rows.append(f"DA read FAIL {e}")
        # BP 캐릭터의 config 참조
        try:
            cfg = pawn.get_editor_property("WallHandConfig")
            rows.append(f"pawn.WallHandConfig = {cfg.get_name() if cfg else None}")
            if cfg:
                rows.append(f"cfg.ElbowAngleDeg = {cfg.get_editor_property('ElbowAngleDeg')}")
        except Exception as e:
            rows.append(f"pawn cfg FAIL {str(e)[:80]}")
        # ABP 변수
        mesh = pawn.get_editor_property("Mesh")
        abp = mesh.get_anim_instance()
        try:
            rows.append(f"ABP.WHElbowRad = {abp.get_editor_property('WHElbowRad')}")
        except Exception as e:
            rows.append(f"ABP var FAIL {str(e)[:80]}")
        # 레이어 인스턴스
        try:
            li = mesh.get_editor_property("LinkedInstances")
            for inst in (li or []):
                nm = inst.get_class().get_name()
                if "Layer" in nm or "IK" in nm:
                    try:
                        rows.append(f"{nm}.WHElbowRad = {inst.get_editor_property('WHElbowRad')}")
                    except Exception:
                        rows.append(f"{nm}: WHElbowRad 없음")
        except Exception as e:
            rows.append(f"layer FAIL {str(e)[:60]}")
        open(OUT, "w", encoding="utf-8").write("\n".join(rows))
    except Exception:
        open(OUT, "w", encoding="utf-8").write("FATAL\n" + traceback.format_exc())
h = unreal.register_slate_post_tick_callback(tick)
