import unreal
DST="/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
bp=unreal.load_asset(DST); ctrl=bp.get_controller_by_name("RigVMModel")
try:
    ctrl.remove_node_by_name("RigVMFunction_Sequence")
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_asset(DST)
    open(r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\rmseq.txt","w").write("removed Sequence + compiled + saved\nnodes="+str([n.get_node_path() for n in ctrl.get_graph().get_nodes()]))
except Exception as e:
    open(r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\rmseq.txt","w").write("ERR "+str(e))
