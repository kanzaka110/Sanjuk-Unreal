# CR SlopeLift 체인 현재 상태 확인 (read-only)
import unreal, json

CR = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_CtrlRig_LedgeDangle"
bp = unreal.load_asset(CR)
c = bp.get_controller_by_name("RigVMModel") or bp.get_controller()
g = c.get_graph()
for nm in ("SlopeLiftWeight", "SlopeLiftMake", "SlopeLiftAdd", "RigUnit_SetTranslation", "VariableNode_4"):
    n = None
    for x in g.get_nodes():
        if str(x.get_node_path()) == nm:
            n = x
    if n is None:
        print(nm, ": MISSING")
        continue
    info = []
    for p in n.get_pins():
        links = [str(l.get_opposite_pin(p).get_pin_path()) for l in p.get_links()]
        if links or str(p.get_name()) in ("Value", "Weight", "A", "B", "X", "Y", "Z", "Item", "Space"):
            d = str(p.get_default_value())[:40]
            info.append("%s(%s) def=%s links=%s" % (p.get_name(), str(p.get_direction()).split(".")[-1][:3], d, links))
    print(nm, "|", " ; ".join(info))
