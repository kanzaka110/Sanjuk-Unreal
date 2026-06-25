import unreal, traceback
OUT=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\probe_damp_pins.txt"
L=[]
def w(s): L.append(str(s))
def dump(tn):
    w(f"\n=== {tn} ===")
    try:
        st=getattr(unreal,tn).static_struct()
        for p in unreal.StructLibrary.get_all_properties(st) if hasattr(unreal,'StructLibrary') else []:
            w("  prop "+str(p))
    except Exception as e:
        w("  (StructLibrary fail) "+str(e))
    # fallback: instantiate and list editor props
    try:
        inst=getattr(unreal,tn)()
        for k in dir(inst):
            if not k.startswith("_") and not callable(getattr(inst,k,None)):
                w("  field "+k)
    except Exception as e:
        w("  (inst fail) "+str(e))
try:
    for tn in ["RigVMFunction_DampVector","RigVMFunction_AlphaInterpVector","RigUnit_AlphaInterpVector"]:
        dump(tn)
except Exception: w(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
