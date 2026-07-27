# 펠비스 리프트 런타임 체크 — ABP 변수 → IK레이어 변수 → 릭 인스턴스 변수 도달 확인
import unreal

w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
mesh = pawn.get_components_by_class(unreal.SkeletalMeshComponent)[0]
anim = mesh.get_anim_instance()
print("ABP LedgeSlopeDzBody =", float(anim.get_editor_property("LedgeSlopeDzBody")))
print("ABP DzL/DzR =", float(anim.get_editor_property("LedgeSlopeDzL")),
      float(anim.get_editor_property("LedgeSlopeDzR")))

ikc = unreal.load_object(None, "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK.PC_01_AnimLayer_IK_C")
try:
    inst = mesh.get_linked_anim_layer_instance_by_class(ikc)
    print("IK layer inst:", inst.get_name() if inst else None)
    if inst:
        print("IK layer LedgeSlopeDzBody =", float(inst.get_editor_property("LedgeSlopeDzBody")))
except Exception as e:
    print("layer inst fail:", repr(e)[:150])

cnt = 0
for o in unreal.ObjectIterator(unreal.ControlRig):
    cn = o.get_class().get_name()
    if "LedgeDangle" in cn:
        cnt += 1
        try:
            v = o.get_editor_property("PelvisSlopeLift")
            print("RIG", o.get_name(), "PelvisSlopeLift =", float(v))
        except Exception as e:
            print("RIG", o.get_name(), "read fail:", repr(e)[:150])
print("rig instances:", cnt)
