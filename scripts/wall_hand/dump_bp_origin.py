import unreal, traceback
OUT=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\dump_bp_origin.txt"
L=[]
def w(s): L.append(str(s))
# locate PC_01_BP
cands=[
 "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP",
 "/Game/Art/Character/PC/PC_01/Blueprint/PC_01",
 "/Game/Art/Character/PC/PC_01/PC_01_BP",
]
try:
    bp=None; path=None
    for c in cands:
        if unreal.EditorAssetLibrary.does_asset_exist(c):
            bp=unreal.load_asset(c); path=c; break
    if bp is None:
        # search registry
        ar=unreal.AssetRegistryHelpers.get_asset_registry()
        for a in ar.get_assets_by_path("/Game/Art/Character/PC/PC_01",recursive=True):
            nm=str(a.asset_name)
            if nm in ("PC_01_BP","PC_01") and "Blueprint" in str(a.asset_class_path.asset_name) or nm.endswith("_BP"):
                w(f"candidate {a.package_name} class={a.asset_class_path.asset_name}")
        raise Exception("PC_01_BP not at known paths; see candidates above")
    w(f"BP={path}")
    # find UpdateWallHandIK function graph
    for fg in unreal.BlueprintEditorLibrary.get_function_graphs(bp) if hasattr(unreal.BlueprintEditorLibrary,'get_function_graphs') else []:
        w("fgraph "+str(fg.get_name()))
except Exception: w(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
