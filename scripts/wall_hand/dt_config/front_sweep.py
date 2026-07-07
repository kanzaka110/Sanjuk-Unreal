# -*- coding: utf-8 -*-
"""정면 팔꿈치 응답 스윕: -60/-30/0/30/60도에서 양팔 팔꿈치 수직오프셋(팔축 기준).
'벌어짐' = 팔꿈치가 몸 바깥(좌우 측면)으로, '붙음' = 몸 안쪽. 액터공간 성분으로 판별."""
import io
import re
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config")
from mono import call

SETD = '''
import unreal
da = unreal.load_object(None,'/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK/DA_WallHandIK.DA_WallHandIK')
MK='ElbowAngleDeg_20_66A3767C467F68D06CC2D2B03CF8E29E'
s=da.get_editor_property('FWall'); s.set_editor_property(MK,VALUE); da.set_editor_property('FWall',s)
'''

PROBE = '''
import unreal
gw=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
cs=[a for a in unreal.GameplayStatics.get_all_actors_of_class(gw,unreal.Character) if a.get_name().startswith('PC_01')]
pc=cs[0]; mesh=pc.get_editor_property('Mesh'); ai=mesh.get_anim_instance()
tf=pc.get_actor_transform()
def L(b):
    v=tf.inverse_transform_location(mesh.get_socket_location(b))
    return [v.x,v.y,v.z]
rad=float(ai.get_editor_property('WHElbowRad'))
out=[]
for side,ua_,el_,hd_ in (('R','upperarm_r','lowerarm_r','hand_r'),('L','upperarm_l','lowerarm_l','hand_l')):
    ua=L(ua_); el=L(el_); hd=L(hd_)
    ax=[hd[k]-ua[k] for k in range(3)]
    mid=[(ua[k]+hd[k])/2 for k in range(3)]
    eb=[el[k]-mid[k] for k in range(3)]
    a2=sum(a*a for a in ax)
    dot=sum(eb[k]*ax[k] for k in range(3))/a2
    perp=[eb[k]-dot*ax[k] for k in range(3)]
    out.append('%s perp=(%.1f,%.1f,%.1f)' % (side,perp[0],perp[1],perp[2]))
print('SWEEP rad=%.2f | %s | %s' % (rad, out[0], out[1]))
'''

PAT = re.compile(r"SWEEP rad=[-0-9.]+ \| R perp=\([-0-9., ]+\) \| L perp=\([-0-9., ]+\)")


def sample(tag):
    err, out = call("editor_query", {"action": "run_python", "command": PROBE}, timeout=25)
    m = PAT.search(out)
    print(f"[{tag}]", m.group(0) if m else out[:90])


for deg in (-60.0, -30.0, 0.0, 30.0, 60.0):
    call("editor_query", {"action": "run_python", "command": SETD.replace("VALUE", str(deg))}, timeout=20)
    time.sleep(1.2)
    sample(f"{deg:+.0f}deg")
