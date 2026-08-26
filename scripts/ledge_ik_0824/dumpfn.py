import sys,json
from mono import *
L="/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_AnimLayer_Ledge"
def dump(fn):
    g=call("blueprint_query","get_graph_data",{"asset_path":L,"graph_name":fn})
    print(f"=== {fn} nodes={len(g['nodes'])}")
    for n in g["nodes"]:
        t=n.get("title","").replace("\n"," | ")
        ins=[]; outs=[]
        for p in n["pins"]:
            c=p.get("connected_to") or []
            if p["direction"]=="input":
                if c: ins.append(f"{p['name']}<-{','.join(x.split('.')[0]+'.'+x.split('.')[-1] if '.' in x else x for x in c)}")
                elif p.get("default_value") not in (None,"","0.0","0, 0, 0","false","None") and p["type"]!="exec": ins.append(f"{p['name']}={p['default_value']}")
            else:
                if c: outs.append(f"{p['name']}->{len(c)}")
        print(f"[{n['id']}] {t} :: {' '.join(ins)} => {' '.join(outs)}")
for fn in sys.argv[1:]: dump(fn)
