import unreal
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/degs_now.txt"
cls = unreal.load_object(None, "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP.PC_01_ABP_C")
cdo = unreal.get_default_object(cls)
L=[]
for n in ("WHSideRotWalkDeg","WHSideRotJogDeg","WHSideRotRunDeg","WHSideRotSprintDeg"):
    L.append(f"{n} = {cdo.get_editor_property(n)}")
open(OUT,"w").write("\n".join(L))
