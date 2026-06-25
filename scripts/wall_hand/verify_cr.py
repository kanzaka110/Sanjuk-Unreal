"""④ v1 CR 검증 (read-only). 노드/링크/멤버변수/컴파일상태 덤프."""
import unreal, traceback
OUT = r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\wallhand_verify.txt"
DST = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
lines = []
def w(s): lines.append(str(s))
try:
    bp = unreal.load_asset(DST)
    ctrl = bp.get_controller_by_name("RigVMModel")
    g = ctrl.get_graph()
    w("=== nodes ===")
    for n in g.get_nodes():
        ss = ""
        try:
            s = n.get_script_struct()
            if s: ss = s.get_name()
        except Exception: pass
        w(f"  {n.get_node_path()}  {ss}")
    w("\n=== links ===")
    for lk in g.get_links():
        w(f"  {lk.get_source_pin().get_pin_path()} -> {lk.get_target_pin().get_pin_path()}")
    w("\n=== member vars (name/type/public) ===")
    for v in bp.get_member_variables():
        try:
            w(f"  {v.get_editor_property('name')} : {v.get_editor_property('cpp_type')} public={v.get_editor_property('public')}")
        except Exception as e:
            w(f"  {v}")
    w("\n=== TwoBoneIK_R key pins ===")
    for n in g.get_nodes():
        if n.get_node_path() == "TwoBoneIK_R":
            for p in n.get_pins():
                nm = p.get_name()
                if nm in ("ItemA","ItemB","EffectorItem","PrimaryAxis","PoleVectorKind","Weight","SecondaryAxisWeight"):
                    w(f"  {nm} = {p.get_default_value()!r}")
                    for sp in p.get_sub_pins():
                        w(f"      .{sp.get_name()} = {sp.get_default_value()!r}")
    w("\n=== compile status ===")
    try:
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        w("  recompiled (no exception)")
    except Exception as e:
        w(f"  compile EXC {str(e)[:80]}")
except Exception:
    w("\n!!! EXC:\n" + traceback.format_exc())
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
unreal.log("[wallhand_verify] done")
