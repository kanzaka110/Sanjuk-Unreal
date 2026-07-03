# -*- coding: utf-8 -*-
"""CR 최적화 v2: exec 도달성 = BeginExecution BFS. 비도달 exec + 고아 데이터 반복 제거."""
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260703_opt/cr_opt2_result.txt"
L=[]
try:
    bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK")
    ctrl = bp.get_controller_by_name("RigVMModel")
    g = ctrl.get_graph()
    def analyze():
        nodes = list(g.get_nodes())
        execmap = {}; inmap = {}
        roots = set()
        for n in nodes:
            nm = n.get_name()
            if "BeginExecution" in nm or "PrepareForExecution" in nm or "InverseExecution" in nm:
                roots.add(nm)
            for p in n.get_pins():
                is_exec = "Execute" in p.get_name()
                for tgt in p.get_linked_target_pins():
                    tn = tgt.get_pin_path().split(".")[0]
                    if is_exec: execmap.setdefault(nm, set()).add(tn)
                for src in p.get_linked_source_pins():
                    sn = src.get_pin_path().split(".")[0]
                    if not is_exec: inmap.setdefault(nm, set()).add(sn)
                for sp in p.get_sub_pins():
                    for src in sp.get_linked_source_pins():
                        inmap.setdefault(nm, set()).add(src.get_pin_path().split(".")[0])
        live = set(roots); stack = list(roots)
        while stack:  # exec 도달
            nm = stack.pop()
            for t in execmap.get(nm, ()):
                if t not in live: live.add(t); stack.append(t)
        stack = list(live)
        while stack:  # 데이터 역방향
            nm = stack.pop()
            for s in inmap.get(nm, ()):
                if s not in live: live.add(s); stack.append(s)
        return [n.get_name() for n in nodes if n.get_name() not in live]
    total = []
    for rnd in range(10):
        dead = analyze()
        if not dead: break
        cnt = 0
        for nm in dead:
            try:
                ctrl.remove_node_by_name(nm); total.append(nm); cnt += 1
            except Exception: pass
        L.append(f"round{rnd}: dead={len(dead)} removed={cnt}")
        if cnt == 0: break
    L.append(f"총 제거 {len(total)}: " + ", ".join(total))
    L.append(f"남은 노드: {len(list(g.get_nodes()))}")
    bp.recompile_vm(); bp.recompile_vm_if_required()
    ok = unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()], False)
    L.append(f"save={ok}")
except Exception:
    L.append(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
