# 렛지 스플라인 참조 획득 경로 실측 (2026-07-23 Phase C 사전조사)
# 목적: 매달림 중 ABP가 BP_EM_Ledge의 LedgeSpline에 닿는 경로 판정
#   A) 캐릭터 오버랩에 렛지 액터가 잡히는가 (매달림 내내 유지되는가)
#   B) 무브먼트 컴포넌트에 은닉 렛지 참조 프로퍼티가 있는가
#   C) 레벨 내 렛지 액터 수 (GetAllActorsOfClass 비용 판단)
# 실행: PIE에서 원통 렛지에 매달린 상태로 실행
import unreal

w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
if w is None:
    print("PIE OFF")
else:
    pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
    mesh = pawn.get_components_by_class(unreal.SkeletalMeshComponent)[0]
    anim = mesh.get_anim_instance()
    lmd = anim.get_editor_property("LedgeMoveData")
    print("ledge_active =", bool(lmd.get_editor_property("bActive")),
          " cur =", float(lmd.get_editor_property("CurrentDistance")))

    # A) 오버랩
    ov = list(pawn.get_overlapping_actors())
    print("A) overlap_total =", len(ov))
    for a in ov:
        cn = a.get_class().get_name()
        sp = a.get_components_by_class(unreal.SplineComponent)
        mark = "  <-- SPLINE" if len(sp) else ""
        print("   ", a.get_name(), cn, mark)

    # B) 무브먼트 은닉 프로퍼티 후보
    mc = pawn.get_movement_component()
    for name in ("CurrentLedgeFeature", "LedgeFeature", "ActiveLedgeFeature",
                 "GrabbedLedge", "CurrentLedge", "LedgeSpline", "CurrentLedgeSpline",
                 "LedgeMoveFeature", "OwnerLedgeFeature"):
        try:
            v = mc.get_editor_property(name)
            print("B) FOUND", name, "=", v)
        except Exception:
            pass
    print("B) probe done")

    # C) 레벨 내 렛지 액터 수 + 최근접 판별 실효성
    cls = unreal.load_object(None,
        "/Game/GameDesign/Level/BluePrintActor/EventMove/BP_EM_Ledge.BP_EM_Ledge_C")
    actors = unreal.GameplayStatics.get_all_actors_of_class(w, cls)
    print("C) BP_EM_Ledge count =", len(actors))
    ploc = pawn.get_actor_location()
    best = None
    for a in actors:
        sps = a.get_components_by_class(unreal.SplineComponent)
        if not len(sps):
            continue
        s = sps[0]
        cp = s.find_location_closest_to_world_location(
            ploc, unreal.SplineCoordinateSpace.WORLD)
        d = ((cp.x - ploc.x) ** 2 + (cp.y - ploc.y) ** 2 + (cp.z - ploc.z) ** 2) ** 0.5
        if best is None or d < best[0]:
            best = (d, a.get_name(), s)
    if best:
        print("C) nearest =", best[1], " dist = %.1f" % best[0])
        s = best[2]
        key = s.find_input_key_closest_to_world_location(ploc)
        dist_at = s.get_distance_along_spline_at_spline_input_key(key)
        print("C) closest_input_key = %.3f  dist_along = %.1f (lmd cur 대조용)" % (float(key), float(dist_at)))
        print("C) spline_length = %.1f  closed_loop =" % float(s.get_spline_length()),
              bool(s.get_editor_property("bClosedLoop")))
