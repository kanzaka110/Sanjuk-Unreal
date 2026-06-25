import unreal, traceback
OUT=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\probe_smoother2.txt"
L=[]
def w(s): L.append(str(s))
try:
    names=[n for n in dir(unreal) if any(k in n.lower() for k in ("spring","damp","interpto","interp")) ]
    rig=[n for n in dir(unreal) if n.startswith("RigVMFunction_Math") or n.startswith("RigUnit_")]
    w("=== interp/spring/damp types in unreal ===")
    for n in names: w("  "+n)
    w("=== RigVMFunction_MathVector* / RigUnit_* (filtered smoothing) ===")
    for n in rig:
        ln=n.lower()
        if any(k in ln for k in ("spring","damp","interp","ease","lerp","blend")):
            w("  "+n)
except Exception: w(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
