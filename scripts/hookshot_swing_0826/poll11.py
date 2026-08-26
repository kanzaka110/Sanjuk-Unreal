import time, sys, json
from mono import call
MAX=float(sys.argv[1]) if len(sys.argv)>1 else 300.0
WANT,TAIL=2,4.0
def cf(comp,fn,**kw):
    p={'class_name':'PC_01','function':fn,'allow_non_callable':True}
    if comp: p['component_name']=comp
    p.update(kw); return call('editor_query','pie_call_function',p,timeout=10)
def abp():
    return call('editor_query','pie_get_object_properties',{'class_name':'PC_01','anim_instance':True,
      'properties':['HookshotPhase','HookshotLandDir','is HookShot','StateMachineMoveState',
                    'BlendStackInputs.Anim','HookLandMontagePicked']},timeout=10)
t0=time.time(); out=[]; prev=None; cyc=0; was=False; done=None
while time.time()-t0<MAX:
    t=round(time.time()-t0,2)
    try:
        raw=cf('CharMoveComp','GetHookshotPhase').get('return_value')
        typ=cf('CharMoveComp','GetHookshotType').get('return_value')
        mtg=cf(None,'GetCurrentActiveMontage',anim_instance=True).get('return_value')
        rec={'t':t,'raw':raw,'typ':typ,'mtg':mtg,'p':abp().get('properties',{})}
    except Exception as e:
        rec={'t':t,'err':str(e)[:140]}; raw=None
    k=json.dumps(rec.get('p'),ensure_ascii=False)+str(rec.get('raw'))+str(rec.get('mtg'))
    if k!=prev: out.append(rec); prev=k
    now=str(raw) not in ('None','none')
    if now and not was: was=True
    if was and not now:
        was=False; cyc+=1
        if cyc>=WANT and done is None: done=time.time()+TAIL
    if done and time.time()>done: break
    time.sleep(0.07)
open('t11.txt','w',encoding='utf-8').write('\n'.join(json.dumps(o,ensure_ascii=False) for o in out))
print("cycles=",cyc,"rows=",len(out))
