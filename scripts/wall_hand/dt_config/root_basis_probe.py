# -*- coding: utf-8 -*-
"""root 본 축 실측(액터 공간) + 폴 방향 검산: 정면 스탠스에서 폴 (-50,0,1)이 액터 기준 어디를 가리키나."""
import io
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config")
from mono import call

PROBE = '''
import unreal
gw=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
cs=[a for a in unreal.GameplayStatics.get_all_actors_of_class(gw,unreal.Character) if a.get_name().startswith('PC_01')]
pc=cs[0]; mesh=pc.get_editor_property('Mesh')
tf=pc.get_actor_transform()
rt=mesh.get_socket_transform('root', unreal.RelativeTransformSpace.RTS_WORLD)
# root 축들을 액터 공간으로
for name,axis in (('rootX',unreal.Vector(1,0,0)),('rootY',unreal.Vector(0,1,0)),('rootZ',unreal.Vector(0,0,1))):
    w=rt.transform_direction(axis)
    a=tf.inverse_transform_direction(w)
    print('AX %s actor=(%.2f,%.2f,%.2f)' % (name,a.x,a.y,a.z))
# 현재 R 폴 디폴트 (-50,0,1)이 액터 기준 어디인가
pole=rt.transform_direction(unreal.Vector(-50,0,1))
pa=tf.inverse_transform_direction(pole)
print('AX poleR0 actor=(%.1f,%.1f,%.1f)' % (pa.x,pa.y,pa.z))
'''

PAT = re.compile(r"AX [A-Za-z0-9]+ actor=\([-0-9., ]+\)")
err, out = call("editor_query", {"action": "run_python", "command": PROBE}, timeout=25)
for m in PAT.finditer(out):
    print(m.group(0))
