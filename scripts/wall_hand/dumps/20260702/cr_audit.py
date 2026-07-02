import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/cr_audit_result.txt"
L = []
try:
    bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK")
    ctrl = bp.get_controller_by_name("RigVMModel")
    g = ctrl.get_graph()
    nodes = list(g.get_nodes())
    name = {n.get_name(): n for n in nodes}
    # 링크 수집
    in_src = {}   # node -> [source nodes] (입력핀의 소스)
    exec_linked = set()
    def pins_all(n):
        out=[]
        def rec(p):
            out.append(p)
            try:
                for sp in p.get_sub_pins(): rec(sp)
            except Exception: pass
        for p in n.get_pins(): rec(p)
        return out
    for n in nodes:
        nm = n.get_name()
        for p in pins_all(n):
            try:
                srcs = p.get_linked_source_pins()
            except Exception: srcs=[]
            for s in srcs:
                sn = s.get_node().get_name()
                in_src.setdefault(nm, []).append(sn)
                if "Execute" in p.get_name() or "ExecutePin" in p.get_pin_path():
                    exec_linked.add(nm); exec_linked.add(sn)
    # 루트 = exec 체인 노드
    live = set(exec_linked)
    stack = list(exec_linked)
    while stack:
        nm = stack.pop()
        for src in in_src.get(nm, []):
            if src not in live:
                live.add(src); stack.append(src)
    dead = [nm for nm in name if nm not in live]
    L.append(f"total={len(nodes)} execlive={len(exec_linked)} live={len(live)} dead={len(dead)}")
    for nm in sorted(dead):
        t=""
        try: t = str(name[nm].get_node_title())
        except Exception: pass
        L.append(f"  DEAD {nm:24s} {t}")
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(L))
