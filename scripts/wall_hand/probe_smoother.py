import unreal, traceback
OUT=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\probe_smoother.txt"
L=[]
def w(s): L.append(str(s))
try:
    # search loaded structs for stateful vector smoothers
    pat=("spring","damp","interpto","deltatime")
    found=[]
    for s in unreal.StructLibrary.__dict__ if hasattr(unreal,'StructLibrary') else []:
        pass
    # brute: try known candidate struct paths
    cands=[
        "/Script/RigVM.RigVMFunction_MathVectorSpringInterp",
        "/Script/RigVM.RigVMFunction_MathFloatSpringInterp",
        "/Script/RigVM.RigVMFunction_MathVectorInterpTo",
        "/Script/ControlRig.RigUnit_DampTransform",
        "/Script/ControlRig.RigUnit_AnimEasing",
        "/Script/RigVM.RigVMFunction_MathTransformSpringInterp",
        "/Script/RigVM.RigVMFunction_MathQuaternionSpringInterp",
    ]
    for c in cands:
        st=unreal.load_object(None, c)
        w(f"{c} -> {'OK' if st else 'None'}")
    # also list struct names containing spring/damp via AssetRegistry not feasible; try reflection on a node
except Exception: w(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
