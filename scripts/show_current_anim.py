import unreal

pc = unreal.GameplayStatics.get_player_controller(unreal.EditorLevelLibrary.get_game_world(), 0)
if pc:
    pawn = pc.get_pawn()
    if pawn:
        mesh = pawn.get_component_by_class(unreal.SkeletalMeshComponent)
        if mesh:
            anim = mesh.get_anim_instance()
            if anim:
                info = anim.get_current_active_montage()
                montage_name = info.get_name() if info else "None"
                print("Montage: " + montage_name)

                # 현재 재생 중인 시퀀스 정보
                names = []
                for i in range(mesh.get_num_anim_instances()):
                    inst = mesh.get_linked_anim_graph_instance_by_tag("") if i > 0 else anim
                    if inst:
                        names.append(inst.get_class().get_name())
                print("AnimInstances: " + str(names))
        else:
            print("No SkeletalMeshComponent")
    else:
        print("No Pawn")
else:
    print("No PlayerController - PIE 실행 중인지 확인")

print("[DONE]")
