# -*- coding: utf-8 -*-
"""ControlRig_3 용의자 판정: 레이어 IKWeightHand_R/L 라이브 0 → 팔꿈치 폴 추종 회복 여부."""
import io
import re
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config")
from mono import call

PROBE = '''
import unreal
gw=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
cs=[a for a in unreal.GameplayStatics.get_all_actors_of_class(gw,unreal.Character) if a.get_name().startswith('PC_01')]
pc=cs[0]; mesh=pc.get_editor_property('Mesh'); ai=mesh.get_anim_instance()
cls=unreal.load_object(None,'/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK.PC_01_AnimLayer_IK_C')
lay=ai.get_linked_anim_layer_instance_by_class(cls)
tf=pc.get_actor_transform()
def L(b):
    v=tf.inverse_transform_location(mesh.get_socket_location(b))
    return [v.x,v.y,v.z]
wR=float(lay.get_editor_property('IKWeightHand_R')); wL=float(lay.get_editor_property('IKWeightHand_L'))
for side,ua_,el_,hd_ in (('R','upperarm_r','lowerarm_r','hand_r'),('L','upperarm_l','lowerarm_l','hand_l')):
    ua=L(ua_); el=L(el_); hd=L(hd_)
    ax=[hd[k]-ua[k] for k in range(3)]
    mid=[(ua[k]+hd[k])/2 for k in range(3)]
    eb=[el[k]-mid[k] for k in range(3)]
    a2=sum(a*a for a in ax)
    dot=sum(eb[k]*ax[k] for k in range(3))/a2
    perp=[eb[k]-dot*ax[k] for k in range(3)]
    print('RES %s wR=%.2f wL=%.2f perp=(%.1f,%.1f,%.1f)' % (side,wR,wL,perp[0],perp[1],perp[2]))
'''

SETW = '''
import unreal
gw=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
cs=[a for a in unreal.GameplayStatics.get_all_actors_of_class(gw,unreal.Character) if a.get_name().startswith('PC_01')]
ai=cs[0].get_editor_property('Mesh').get_anim_instance()
cls=unreal.load_object(None,'/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK.PC_01_AnimLayer_IK_C')
lay=ai.get_linked_anim_layer_instance_by_class(cls)
lay.set_editor_property('IKWeightHand_R', VALUE)
lay.set_editor_property('IKWeightHand_L', VALUE)
print('SETW', VALUE)
'''

PAT = re.compile(r"RES [RL] wR=[-0-9.]+ wL=[-0-9.]+ perp=\([-0-9., ]+\)")


def sample(tag):
    err, out = call("editor_query", {"action": "run_python", "command": PROBE}, timeout=25)
    for m in PAT.finditer(out):
        print(f"[{tag}]", m.group(0))


# 현재 FWall Elbow=50도 상태여야 함
sample("현재(w원본)")
err, out = call("editor_query", {"action": "run_python",
                                 "command": SETW.replace("VALUE", "0.0")}, timeout=20)
print("IKWeightHand=0 주입:", "SETW" in out)
time.sleep(1.5)
sample("w=0")
# 원복
call("editor_query", {"action": "run_python", "command": SETW.replace("VALUE", "1.0")}, timeout=20)
print("원복 w=1")
