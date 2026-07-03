# -*- coding: utf-8 -*-
"""CR 최적화: PalmAim 꼬리 절단 → dead 반복 제거 (live 소비자 있는 노드는 자동 보존)."""
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260703_opt/cr_opt_result.txt"
L=[]
try:
    bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK")
    ctrl = bp.get_controller_by_name("RigVMModel")
    g = ctrl.get_graph()
    # 1) PalmAim exec 꼬리 절단
    try:
        ctrl.break_link("TwoBoneIK_L.ExecutePin", "PalmAim.ExecutePin")
        L.append("exec 절단: TwoBoneIK_L -x-> PalmAim")
    except Exception as e:
        L.append(f"exec 절단 skip: {str(e)[:60]}")
    # 2) dead 반복 제거
    def compute_dead():
        nodes = list(g.get_nodes())
        by = {n.get_name(): n for n in nodes}
        live = set(); inmap = {}
        for n in nodes:
            nm = n.get_name()
            has_exec = False
            for p in n.get_pins():
                pn = p.get_name()
                if "Execute" in pn:
                    if p.get_linked_source_pins() or p.get_linked_target_pins():
                        has_exec = True
                for src in p.get_linked_source_pins():
                    inmap.setdefault(nm, set()).add(src.get_pin_path().split(".")[0])
                for sp in p.get_sub_pins():
                    for src in sp.get_linked_source_pins():
                        inmap.setdefault(nm, set()).add(src.get_pin_path().split(".")[0])
            if has_exec or "BeginExecution" in nm:
                live.add(nm)
        stack = list(live)
        while stack:
            nm = stack.pop()
            for s in inmap.get(nm, ()):
                if s not in live:
                    live.add(s); stack.append(s)
        return [n.get_name() for n in nodes if n.get_name() not in live]
    total_removed = []
    for rnd in range(10):
        dead = compute_dead()
        if not dead: break
        removed_this = 0
        for nm in dead:
            try:
                ctrl.remove_node_by_name(nm)
                total_removed.append(nm); removed_this += 1
            except Exception:
                pass  # 이미 연쇄 삭제됨
        L.append(f"round{rnd}: dead={len(dead)} removed={removed_this}")
        if removed_this == 0: break
    L.append(f"총 제거: {len(total_removed)}")
    L.append("제거 목록: " + ", ".join(total_removed))
    L.append(f"남은 노드: {len(list(g.get_nodes()))}")
    bp.recompile_vm(); bp.recompile_vm_if_required()
    ok = unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()], False)
    L.append(f"save={ok}")
except Exception:
    L.append(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
