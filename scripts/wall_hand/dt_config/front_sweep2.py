# -*- coding: utf-8 -*-
"""정밀 스윕: DA 세팅 후 WHElbowRad가 기대 rad에 도달할 때까지 폴링 후 팔꿈치 측정."""
import io
import math
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

MEASURE = '''
import unreal
gw=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
cs=[a for a in unreal.GameplayStatics.get_all_actors_of_class(gw,unreal.Character) if a.get_name().startswith('PC_01')]
pc=cs[0]; mesh=pc.get_editor_property('Mesh'); ai=mesh.get_anim_instance()
rad=float(ai.get_editor_property('WHElbowRad'))
tf=pc.get_actor_transform()
def L(b):
    v=tf.inverse_transform_location(mesh.get_socket_location(b))
    return [v.x,v.y,v.z]
res=[]
for side,ua_,el_,hd_ in (('R','upperarm_r','lowerarm_r','hand_r'),('L','upperarm_l','lowerarm_l','hand_l')):
    ua=L(ua_); el=L(el_); hd=L(hd_)
    ax=[hd[k]-ua[k] for k in range(3)]
    mid=[(ua[k]+hd[k])/2 for k in range(3)]
    eb=[el[k]-mid[k] for k in range(3)]
    a2=sum(a*a for a in ax)
    dot=sum(eb[k]*ax[k] for k in range(3))/a2
    perp=[eb[k]-dot*ax[k] for k in range(3)]
    res.append('%sY=%.1f' % (side,perp[1]))
print('M rad=%.3f %s %s' % (rad, res[0], res[1]))
'''

PAT = re.compile(r"M rad=([-0-9.]+) RY=([-0-9.]+) LY=([-0-9.]+)")


def measure():
    err, out = call("editor_query", {"action": "run_python", "command": MEASURE}, timeout=25)
    return PAT.search(out)


for deg in (-60.0, -30.0, 0.0, 30.0, 60.0):
    call("editor_query", {"action": "run_python", "command": SETD.replace("VALUE", str(deg))}, timeout=20)
    want = math.radians(deg)
    ok = False
    for _ in range(8):
        time.sleep(0.6)
        m = measure()
        if m and abs(float(m.group(1)) - want) < 0.02:
            print(f"[{deg:+.0f}deg] rad={m.group(1)} RY={m.group(2)} LY={m.group(3)}")
            ok = True
            break
    if not ok:
        print(f"[{deg:+.0f}deg] 미도달 (마지막: {m.group(0) if m else 'None'})")
