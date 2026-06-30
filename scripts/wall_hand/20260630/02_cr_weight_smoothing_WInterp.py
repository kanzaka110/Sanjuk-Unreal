import unreal,traceback
CR="/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
OUT=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\f525ae6b-fccb-4356-b678-43eef9ec8640\scratchpad\cr_weight_smooth.txt"
L=[]
def w(s): L.append(str(s)); open(OUT,"w",encoding="utf-8").write("\n".join(L))
try:
    bp=unreal.load_asset(CR)
    # P4 checkout
    try:
        unreal.EditorAssetLibrary.checkout_loaded_asset(bp); w("checkout requested")
    except Exception as e: w("checkout skip %s"%str(e)[:40])
    ctrl=bp.get_controller_by_name("RigVMModel");g=ctrl.get_graph()
    AI="/Script/ControlRig.RigUnit_AlphaInterp"
    def have(n): return any(x.get_node_path()==n for x in g.get_nodes())
    def addn(name,x,y):
        if not have(name):
            n=ctrl.add_unit_node_from_struct_path(AI,"Execute",unreal.Vector2D(x,y),name); w("add %s=%s"%(name,n.get_node_path() if n else "FAIL"))
        else: w("%s exists"%name)
    def setp(p,v):
        try: ctrl.set_pin_default_value(p,v,False); 
        except Exception as e: w("set %s ERR %s"%(p,str(e)[:40]))
    def brk(s,t):
        try: ctrl.break_link(s,t)
        except Exception as e: w("brk ERR %s"%str(e)[:40])
    def link(s,t):
        try: ctrl.add_link(s,t)
        except Exception as e: w("link %s->%s ERR %s"%(s,t,str(e)[:50]))
    for nm,sel,ik,y in (("WInterpR","SelR","TwoBoneIK_R",100),("WInterpL","SelL","TwoBoneIK_L",260)):
        addn(nm,3800,y)
        setp("%s.bInterpResult"%nm,"True")
        setp("%s.InterpSpeedIncreasing"%nm,"8.000000")
        setp("%s.InterpSpeedDecreasing"%nm,"8.000000")
        link("%s.Result"%sel,"%s.Value"%nm)
        brk("%s.Result"%sel,"%s.Weight"%ik)
        link("%s.Result"%nm,"%s.Weight"%ik)
    bp.recompile_vm()
    pkg=bp.get_package()
    pkg.set_dirty_flag(True)
    ok=unreal.EditorLoadingAndSavingUtils.save_packages([pkg],False); w("save_packages=%s"%ok)
    # verify in-memory
    m={}
    for lk in g.get_links(): m.setdefault(lk.get_target_pin().get_pin_path(),[]).append(lk.get_source_pin().get_pin_path())
    w("VERIFY R.Weight<-%s  L.Weight<-%s"%(m.get("TwoBoneIK_R.Weight"),m.get("TwoBoneIK_L.Weight")))
    w("WInterpR.Value<-%s  WInterpL.Value<-%s"%(m.get("WInterpR.Value"),m.get("WInterpL.Value")))
    w("DONE")
except Exception: w(traceback.format_exc())
unreal.log("ws2 done")
