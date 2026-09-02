# -*- coding: utf-8 -*-
"""LedgePhysDebugs 배선 + 기본값"""
from mono import *
L='/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_AnimLayer_Ledge'
FN='LedgePhysDebugs'
bq=lambda a,p: call('blueprint_query',a,p)
def Q(**kw): return dict(asset_path=L, graph_name=FN, **kw)
def con(s,sp,t,tp):
    r=bq('connect_pins',Q(source_node=s,source_pin=sp,target_node=t,target_pin=tp))
    ok=r.get('success',True); print(('  ok  ' if ok else '  FAIL'),s,sp,'->',t,tp)
    return ok
def dflt(n,pin,v):
    bq('set_pin_default',Q(node_id=n,pin_name=pin,value=v)); print('  dflt',n,pin,'=',repr(v))

ENTRY='K2Node_FunctionEntry_0'; BR='K2Node_IfThenElse_0'; GV='K2Node_VariableGet_0'
ML='K2Node_VariableGet_7'; MKV='K2Node_CallFunction_6'; ADDV='K2Node_CallFunction_7'
DDS='K2Node_CallFunction_8'
BS=['K2Node_CallFunction_%d'%i for i in range(6)]
VG=['K2Node_VariableGet_%d'%i for i in range(1,7)]
VAR=['LedgePhysWanted','LedgePhysProfileOn','LedgePhysicsActive',
     'LedgeDangleAlpha','LedgePhysAnimAlpha','LedgePhysicsElapsed']
VPIN=['InBool']*3+['InDouble']*3
LAB=['W:',' On:',' Act:',' Dangle:',' AnimA:',' Elap:']

print('- exec/게이트')
con(ENTRY,'then',BR,'execute'); con(GV,'LedgeDebug',BR,'Condition'); con(BR,'then',DDS,'execute')
print('- 문자열 체인')
for i in range(6):
    con(VG[i],VAR[i],BS[i],VPIN[i]); dflt(BS[i],'Prefix',LAB[i])
    if i: con(BS[i-1],'ReturnValue',BS[i],'AppendTo')
dflt(BS[0],'AppendTo','PHY ')
con(BS[5],'ReturnValue',DDS,'Text')
print('- 위치(MeshLocation +Z40)')
for ax,val in (('X','0.0'),('Y','0.0'),('Z','40.0')): dflt(MKV,ax,val)
con(ML,'MeshLocation',ADDV,'A'); con(MKV,'ReturnValue',ADDV,'B'); con(ADDV,'ReturnValue',DDS,'TextLocation')
dflt(DDS,'TextColor','(R=1.000000,G=0.550000,B=0.100000,A=1.000000)')
dflt(DDS,'Duration','0.000000')
c=bq('compile_blueprint',{'asset_path':L}); print('COMPILE',c.get('success'),c.get('errors'),c.get('warnings'))
