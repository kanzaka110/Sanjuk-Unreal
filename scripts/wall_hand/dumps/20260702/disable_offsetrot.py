import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/offsetrot_off.txt"
L=[]
try:
    bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK")
    ctrl = bp.get_controller_by_name("RigVMModel")
    g = ctrl.get_graph()
    nodes = {n.get_name(): n for n in g.get_nodes()}
    for nm in ("OffsetRotR","OffsetRotL"):
        for p in nodes[nm].get_pins():
            if p.get_name()=="Weight":
                for s in p.get_linked_source_pins():
                    ctrl.break_link(s.get_pin_path(), f"{nm}.Weight")
                    L.append(f"break {s.get_pin_path()} -> {nm}.Weight")
        ctrl.set_pin_default_value(f"{nm}.Weight", "0.0")
        L.append(f"{nm}.Weight=0")
    bp.recompile_vm(); bp.recompile_vm_if_required()
    ok = unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()], False)
    L.append(f"save={ok}")
except Exception:
    L.append(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
