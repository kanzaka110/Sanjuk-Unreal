import unreal,traceback
CR="/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
OUT=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\f525ae6b-fccb-4356-b678-43eef9ec8640\scratchpad\cr_front_build.txt"
L=[]
def w(s):
    L.append(str(s)); open(OUT,"w",encoding="utf-8").write("\n".join(L))
try:
    bp=unreal.load_asset(CR); ctrl=bp.get_controller_by_name("RigVMModel"); g=ctrl.get_graph()
    # current srcmap
    def srcmap():
        m={}
        for lk in g.get_links(): m.setdefault(lk.get_target_pin().get_pin_path(),[]).append(lk.get_source_pin().get_pin_path())
        return m
    # read ToRig Space param to mirror
    torig_space=None
    for n in g.get_nodes():
        if n.get_node_path()=="ToRig":
            for p in n.get_pins():
                if p.get_name() in ("Space",): torig_space=p.get_default_value()
    w("ToRig.Space=%r"%torig_space)
    have={n.get_node_path() for n in g.get_nodes()}
    w("pre nodes ToRigL?%s fSel?%s"%("ToRigL" in have,"fSel" in have))
    # 1) ToRigL
    if "ToRigL" not in have:
        n=ctrl.add_unit_node_from_struct_path("/Script/ControlRig.RigUnit_ToRigSpace_Location","Execute",unreal.Vector2D(-1200,1400),"ToRigL")
        w("ToRigL added=%s"%(n.get_node_path() if n else None))
    if torig_space is not None:
        try: ctrl.set_pin_default_value("ToRigL.Space",torig_space,True); w("ToRigL.Space set")
        except Exception as e: w("ToRigL.Space ERR %s"%str(e)[:80])
    try: ctrl.bind_pin_to_variable("ToRigL.Value","WallHandTargetL",unreal.Vector2D(-1450,1450)); w("bind ToRigL.Value<-WallHandTargetL OK")
    except Exception as e: w("bind ToRigL.Value ERR %s"%str(e)[:120])
    # 2) rewire TwoBoneIK_L.Effector.Translation <- ToRigL.Global
    m=srcmap(); cur=m.get("TwoBoneIK_L.Effector.Translation")
    w("L.Effector.Translation cur src=%s"%cur)
    if cur:
        for s in cur:
            try: ctrl.break_link(s,"TwoBoneIK_L.Effector.Translation"); w("broke %s"%s)
            except Exception as e: w("break ERR %s"%str(e)[:80])
    try: ctrl.add_link("ToRigL.Global","TwoBoneIK_L.Effector.Translation"); w("link ToRigL.Global->L.Effector OK")
    except Exception as e: w("link L.Effector ERR %s"%str(e)[:120])
    # 3) fSel gating
    if "fSel" not in {n.get_node_path() for n in g.get_nodes()}:
        n=ctrl.add_unit_node_from_struct_path("/Script/RigVM.RigVMFunction_MathFloatSelectBool","Execute",unreal.Vector2D(-700,900),"fSel")
        w("fSel added=%s"%(n.get_node_path() if n else None))
    try:
        ctrl.set_pin_default_value("fSel.IfTrue","1.000000",False)
        ctrl.set_pin_default_value("fSel.IfFalse","0.000000",False)
        w("fSel IfTrue/IfFalse set")
    except Exception as e: w("fSel defaults ERR %s"%str(e)[:80])
    try: ctrl.bind_pin_to_variable("fSel.Condition","bWallHandFront",unreal.Vector2D(-950,950)); w("bind fSel.Condition<-bWallHandFront OK")
    except Exception as e: w("bind fSel.Condition ERR %s"%str(e)[:120])
    for tgt in ["SelR.IfFalse","SelL.IfTrue","SelR_1.IfFalse","SelL_1.IfTrue"]:
        try: ctrl.add_link("fSel.Result",tgt); w("link fSel.Result->%s OK"%tgt)
        except Exception as e: w("link %s ERR %s"%(tgt,str(e)[:90]))
    # 4) recompile + save
    try:
        bp.recompile_vm(); 
        if hasattr(bp,"recompile_vm_if_required"): bp.recompile_vm_if_required()
        w("recompiled")
    except Exception as e: w("recompile ERR %s"%str(e)[:120])
    try:
        ok=unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()],False); w("save_packages=%s"%ok)
    except Exception as e: w("save ERR %s"%str(e)[:120])
    w("DONE")
except Exception:
    w(traceback.format_exc())
unreal.log("cr_front_build done")
