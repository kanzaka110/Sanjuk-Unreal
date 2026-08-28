# -*- coding: utf-8 -*-
"""이동 중 물리 게이트가 왜 닫히는지 화면 출력
   'A=<bActive> F=<bFrontBlocked> W=<LedgePhysWanted>'"""
from mono import *
L='/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_AnimLayer_Ledge'; G='LedgeIK'
bq=lambda a,p: call('blueprint_query',a,p)
P=lambda **k: dict(asset_path=L,graph_name=G,**k)
def snap():
    d=bq('get_graph_data',{'asset_path':L,'graph_name':G}); s=set()
    for n in d['nodes']:
        for p in n['pins']:
            if p['direction']=='output':
                for c in p['connected_to']: s.add((n['id'],p['name'],c))
    return d,s
def add(nt,pos,**kw):
    pos=[int(pos[0]),int(pos[1])]
    p=P(node_type=nt,position=pos); p.update(kw)
    rid=bq('add_node',p)['id']
    d,_=snap(); N={n['id']:n for n in d['nodes']}
    if rid in N: return rid
    c=[i for i,n in N.items() if n['pos']==pos]; return c[-1]
def con(s,sp,t,tp):
    r=bq('connect_pins',P(source_node=s,source_pin=sp,target_node=t,target_pin=tp))
    ok=r.get('success',True)
    if not ok: print('  FAIL %s.%s->%s.%s'%(s,sp,t,tp))
    return ok
def dflt(n,pin,v): bq('set_pin_default',P(node_id=n,pin_name=pin,value=v))

before,cb=snap(); N0={n['id']:n for n in before['nodes']}
BX,BY=784,900
KM='KismetStringLibrary'
b2s=lambda pos: add('CallFunction',pos,function_name='Conv_BoolToString',target_class=KM)
cat=lambda pos: add('CallFunction',pos,function_name='Concat_StrStr',target_class=KM)
# bool -> string
sA=b2s((BX,BY)); sF=b2s((BX,BY+80)); sW=b2s((BX,BY+160))
c1=cat((BX+240,BY)); c2=cat((BX+400,BY)); c3=cat((BX+560,BY)); c4=cat((BX+720,BY)); c5=cat((BX+880,BY))
ps=add('CallFunction',(BX+1120,BY-40),function_name='PrintString',target_class='KismetSystemLibrary')
gW=add('VariableGet',(BX-200,BY+200),variable_name='LedgePhysWanted')
print('노드:',sA,sF,sW,c1,c2,c3,c4,c5,ps,gW)
# 값 소스: BreakStruct_1 의 bActive / bFrontBlocked
con('K2Node_BreakStruct_1','bActive',sA,'InBool')
con('K2Node_BreakStruct_1','bFrontBlocked',sF,'InBool')
con(gW,'LedgePhysWanted',sW,'InBool')
dflt(c1,'A','A='); con(sA,'ReturnValue',c1,'B')
con(c1,'ReturnValue',c2,'A'); dflt(c2,'B',' F=')
con(c2,'ReturnValue',c3,'A'); con(sF,'ReturnValue',c3,'B')
con(c3,'ReturnValue',c4,'A'); dflt(c4,'B',' W=')
con(c4,'ReturnValue',c5,'A'); con(sW,'ReturnValue',c5,'B')
con(c5,'ReturnValue',ps,'InString')
dflt(ps,'Duration','0.0')
# exec 삽입: VariableSet_0 -> [PrintString] -> CallFunction_130
bq('disconnect_pins',P(source_node='K2Node_VariableSet_0',source_pin='then',target_node='K2Node_CallFunction_130',target_pin='execute'))
con('K2Node_VariableSet_0','then',ps,'execute')
con(ps,'then','K2Node_CallFunction_130','execute')
after,ca=snap(); N={n['id']:n for n in after['nodes']}
print()
print('노드',len(before['nodes']),'->',len(after['nodes']),'| 연결',len(cb),'->',len(ca))
print('사라진',len(cb-ca),'새',len(ca-cb))
print()
print('PrintString 입력:',{p['name']:(p['connected_to'] or p.get('default_value')) for p in N[ps]['pins'] if p['direction']=='input' and p['name'] in ('InString','Duration','execute')})
c=bq('compile_blueprint',{'asset_path':L})
print('compile:',{k:c[k] for k in ('success','error_count','warning_count') if k in c})
