import unreal,traceback
CR="/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
OUT=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\f525ae6b-fccb-4356-b678-43eef9ec8640\scratchpad\regate_offrot.txt"
L=[]
def w(s): L.append(str(s)); open(OUT,"w",encoding="utf-8").write("\n".join(L))
try:
    bp=unreal.load_asset(CR);ctrl=bp.get_controller_by_name("RigVMModel");g=ctrl.get_graph()
    def brk(s,t):
        try: ctrl.break_link(s,t); w("brk %s->%s"%(s,t))
        except Exception as e: w("brk %s skip(%s)"%(t,str(e)[:40]))
    def link(s,t):
        try: ctrl.add_link(s,t); w("link %s->%s OK"%(s,t))
        except Exception as e: w("link %s->%s ERR %s"%(s,t,str(e)[:50]))
    brk("fSel.Result","OffsetRotR.Weight"); link("SelR.Result","OffsetRotR.Weight")
    brk("fSel.Result","OffsetRotL.Weight"); link("SelL.Result","OffsetRotL.Weight")
    bp.recompile_vm()
    if hasattr(bp,"recompile_vm_if_required"): bp.recompile_vm_if_required()
    ok=unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()],False); w("save=%s"%ok)
    m={}
    for lk in g.get_links(): m.setdefault(lk.get_target_pin().get_pin_path(),[]).append(lk.get_source_pin().get_pin_path())
    w("VERIFY OffsetRotR.Weight<-%s"%m.get("OffsetRotR.Weight"))
    w("VERIFY OffsetRotL.Weight<-%s"%m.get("OffsetRotL.Weight"))
    w("DONE")
except Exception: w(traceback.format_exc())
unreal.log("regate done")
