import unreal,traceback
CR="/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
OUT=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\f525ae6b-fccb-4356-b678-43eef9ec8640\scratchpad\cr_offset_clean.txt"
L=[]
def w(s): L.append(str(s)); open(OUT,"w",encoding="utf-8").write("\n".join(L))
try:
    bp=unreal.load_asset(CR);ctrl=bp.get_controller_by_name("RigVMModel");g=ctrl.get_graph()
    def srcs(t):
        return [lk.get_source_pin().get_pin_path() for lk in g.get_links() if lk.get_target_pin().get_pin_path()==t]
    def brk(s,t):
        try: ctrl.break_link(s,t); w("brk %s->%s"%(s,t))
        except Exception as e: w("brk %s skip"%t)
    def link(s,t):
        try: ctrl.add_link(s,t); w("link %s->%s OK"%(s,t))
        except Exception as e: w("link %s->%s ERR %s"%(s,t,str(e)[:50]))
    # regate weights
    for nd,sel in (("OffsetRotR","SelR.Result"),("OffsetRotL","SelL.Result")):
        for s in srcs("%s.Weight"%nd): brk(s,"%s.Weight"%nd)
        link(sel,"%s.Weight"%nd)
        # zero translation
        try:
            ctrl.set_pin_default_value("%s.OffsetTransform.Translation"%nd,"(X=0.000000,Y=0.000000,Z=0.000000)",True); w("%s.Trans=0"%nd)
        except Exception as e: w("%s.Trans ERR %s"%(nd,str(e)[:50]))
    bp.recompile_vm()
    if hasattr(bp,"recompile_vm_if_required"): bp.recompile_vm_if_required()
    ok=unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()],False); w("save=%s"%ok)
    # verify
    for nd in ("OffsetRotR","OffsetRotL"):
        w("VERIFY %s.Weight<-%s"%(nd,srcs("%s.Weight"%nd)))
        for n in g.get_nodes():
            if n.get_node_path()==nd:
                for p in n.get_pins():
                    if p.get_name()=="OffsetTransform":
                        for sp in p.get_sub_pins():
                            if sp.get_name() in ("Translation","Rotation"): w("   %s.%s=%s"%(nd,sp.get_name(),sp.get_default_value()))
    w("DONE")
except Exception: w(traceback.format_exc())
unreal.log("offset clean done")
