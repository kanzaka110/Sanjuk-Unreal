"""⑤ PC_01_AnimLayer_IK 'IK' 그래프 anim 노드 체인 압축 덤프 (인터페이스 그래프 경유)."""
import unreal, traceback
OUT = r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\ik_animgraph.txt"
PATH = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK"
lines = []
def w(s): lines.append(str(s))

def collect_graphs(abp):
    found = {}
    def addg(g):
        try:
            found[g.get_name()] = g
        except Exception:
            pass
    for prop in ("function_graphs", "ubergraph_pages", "macro_graphs", "delegate_signature_graphs", "intermediate_generated_graphs"):
        try:
            for g in (abp.get_editor_property(prop) or []):
                addg(g)
        except Exception:
            pass
    try:
        for impl in (abp.get_editor_property("implemented_interfaces") or []):
            try:
                for g in (impl.get_editor_property("graphs") or []):
                    addg(g)
            except Exception:
                pass
    except Exception as e:
        w(f"impl_iface ERR {str(e)[:60]}")
    return found

def main():
    abp = unreal.load_asset(PATH)
    graphs = collect_graphs(abp)
    w(f"graphs found: {list(graphs.keys())}")
    g = graphs.get("IK")
    if g is None:
        w("IK not found"); return
    nodes = g.get_nodes()
    w(f"\nIK: {len(nodes)} nodes (anim 노드 위주)")
    for n in nodes:
        cls = n.get_class().get_name()
        if "Comment" in cls or "Knot" in cls:
            continue
        title = ""
        try:
            title = n.get_node_title(unreal.NodeTitleType.LIST_VIEW).replace("\n", " ")
        except Exception:
            pass
        extra = ""
        for prop in ("control_rig_class", "node"):
            try:
                v = n.get_editor_property(prop)
                if v is not None and "control_rig" in prop:
                    extra += f" rig={v.get_name() if hasattr(v,'get_name') else v}"
            except Exception:
                pass
        w(f"  [{cls}] {title}{extra} ::{n.get_name()}")

try:
    main()
except Exception:
    w("\n!!! EXC:\n" + traceback.format_exc())
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
unreal.log("[ik_dump] done")
