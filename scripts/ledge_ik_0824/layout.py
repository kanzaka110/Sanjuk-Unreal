# 승호 정리 패턴 자동 레이아웃: exec 한 줄, 순수 입력은 소비자 아래-왼쪽 깊이별 열, VariableGet 최좌
import sys
from mono import *
DX=230; DY=64; BAND_GAP=120; ROW_GAP=96
def layout(asset,fn,dry=False):
    bq=lambda a,p: call("blueprint_query",a,p)
    g=bq("get_graph_data",{"asset_path":asset,"graph_name":fn}); N={n["id"]:n for n in g["nodes"]}
    isexec=lambda n: any(p["type"]=="exec" for p in n["pins"])
    # exec 순서: 엔트리부터 DFS(then→else 순)
    entry=[i for i,n in N.items() if "FunctionEntry" in n["class"] or n["class"]=="K2Node_Event"][0]
    order=[]; seen=set()
    def dfs(i):
        if i in seen or i not in N: return
        seen.add(i); order.append(i)
        outs=[p for p in N[i]["pins"] if p["type"]=="exec" and p["direction"]=="output"]
        outs.sort(key=lambda p: (p["name"]!="then", p["name"]))
        for p in outs:
            for c in p.get("connected_to") or []: dfs(c.split(".")[0])
    dfs(entry)
    order=[i for i in order if 'Knot' not in i]
    pos={}; placed=set()
    def inputs(i):
        r=[]
        for p in N[i]["pins"]:
            if p["direction"]=="input" and p["type"]!="exec":
                for c in p.get("connected_to") or []:
                    s=c.split(".")[0]
                    if s in N and not isexec(N[s]) and s not in placed: r.append(s)
        return r
    def place_tree(i,x,y):
        """i의 순수 입력 서브트리를 (x,y) 기준 왼쪽 아래로 배치. 사용한 행 수 반환"""
        rows=0
        for s in inputs(i):
            placed.add(s); pos[s]=(x-DX, y+rows*DY)
            sub=place_tree(s,x-DX,y+rows*DY)
            rows+=max(1,sub)
        return rows
    x=0
    for i in order:
        pos[i]=(x,0); placed.add(i)
        n=place_tree(i,x,DY)
        # 밴드 폭: 서브트리 최대 깊이
        def depth(i):
            d=0
            for s in inputs_all(i): d=max(d,1+depth(s))
            return d
        x+= BAND_GAP + DX*max(1,depth_of(i,N,isexec))
    # 고아(미연결) 노드는 맨 아래 행
    oy=DY*12
    for i in N:
        if i not in pos: pos[i]=(0,oy); oy+=DY
    if dry: 
        for i,(px,py) in pos.items(): print(i,px,py)
        return pos
    for i,(px,py) in pos.items():
        if "Knot" in i: continue
        bq("set_node_position",{"asset_path":asset,"graph_name":fn,"node_id":i,"position":[int(px),int(py)]})
    return pos
def depth_of(i,N,isexec,seen=None):
    seen=seen or set(); d=0
    for p in N[i]["pins"]:
        if p["direction"]=="input" and p["type"]!="exec":
            for c in p.get("connected_to") or []:
                s=c.split(".")[0]
                if s in N and not isexec(N[s]) and s not in seen:
                    seen.add(s); d=max(d,1+depth_of(s,N,isexec,seen))
    return d
inputs_all=lambda i: []
if __name__=="__main__":
    layout(sys.argv[1],sys.argv[2],dry=len(sys.argv)>3)
