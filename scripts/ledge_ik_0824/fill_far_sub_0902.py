# -*- coding: utf-8 -*-
"""LedgeMoving 의 Far 중첩(0행)을 Crossing_Far 로 채움 (9/2)
   Crossing 서브(Near)의 행 구성을 그대로 복제하고 애님만 Near→Far 로 교체.
   컬럼: ang(FloatRange) / bFrontBlocked / bTransitMoving / bTransitingToNextLedge / bNextFrontBlocked
"""
import mono; mono.URL='http://127.0.0.1:9316/mcp'
from mono import call
import os
ch=lambda a,p: call('chooser_query',a,p)
B='/Game/Art/Character/PC/PC_01/StateMachine/CustomMove/LedgeMoving.LedgeMoving:'
ANI='/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing/'
SRC=r'E:\Perforce\SB2\Workspace\Internal\SB2\Content\Art\Character\PC\PC_01\Animation\Body\LedgeClimbing'
disk={f[:-7] for f in os.listdir(SRC) if f.endswith('.uasset')}

src=ch('inspect_chooser',{'asset_path':B+'Crossing','include_cells':True})
scols=[(c['index'],c['type'],(c.get('input_binding') or {}).get('display')) for c in src['columns'] if c['type']!='OutputStructColumn']
scells={c['index']:{x['row']:x for x in (c.get('cells') or [])} for c in src['columns']}
sassets={a['row']:(a['asset'].split('/')[-1].split('.')[0] if a['asset'] else None) for a in src['referenced_assets']}
print('원본 Crossing:',src['row_count'],'행 | 입력컬럼',[c[2] for c in scols])

# Far 서브에 동일 컬럼 생성
dst=ch('inspect_chooser',{'asset_path':B+'Far'})
print('Far 현재:',dst['row_count'],'행',dst['column_count'],'컬럼')
if dst['column_count']==0:
    for idx,typ,binding in scols:
        kind={'FloatRangeColumn':'FloatRange','BoolColumn':'Bool','EnumColumn':'Enum'}[typ]
        r=ch('add_chooser_column',{'asset_path':B+'Far','column_kind':kind,'binding_property':binding})
        print('   +col%d %-12s %s'%(r['column_index'],kind,binding))

# 행 복제 (애님 있는 행만, Near→Far)
made=miss=0
for r in range(src['row_count']):
    anim=sassets.get(r)
    if not anim: continue
    far=anim.replace('Crossing_Near_','Crossing_Far_')
    # _0_01 / _0_02 변형은 Far 에 대응 에셋이 없다
    if far not in disk:
        print('   skip(에셋없음)',far.replace('P_Player_Ledge_','')); miss+=1; continue
    cells=[]
    for idx,typ,binding in scols:
        c=scells.get(idx,{}).get(r)
        if typ=='FloatRangeColumn': cells.append({'min':c['min'],'max':c['max']} if c else {'min':-1e30,'max':3.402823466e38})
        else:
            v=str((c or {}).get('value')).lower()
            cells.append(True if v=='true' else False)
    try:
        ch('add_chooser_row',{'asset_path':B+'Far','cells':cells,'output_psd':ANI+far}); made+=1
    except Exception as e:
        print('   FAIL',far,str(e)[:100])
after=ch('inspect_chooser',{'asset_path':B+'Far'})
print('완료: %d행 생성 (대응 에셋 없어 건너뜀 %d) → Far %d행'%(made,miss,after['row_count']))
