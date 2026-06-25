"""CR exec 토폴로지 정밀 덤프: PalmAim/TwoBoneIK/Sequence 의 exec 핀 + 연결."""
import unreal, traceback
OUT = r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\dump_exec.txt"
DST = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
lines=[]
def w(s): lines.append(str(s))
try:
    bp=unreal.load_asset(DST); ctrl=bp.get_controller_by_name("RigVMModel"); g=ctrl.get_graph()
    for n in g.get_nodes():
        np=n.get_node_path()
        if np in ("RigUnit_BeginExecution","TwoBoneIK_R","PalmAim","RigVMFunction_Sequence"):
            w(f"\n[{np}] {n.get_class().get_name()}")
            for p in n.get_pins():
                try:
                    d=p.get_direction()
                    is_exec = "Execute" in p.get_cpp_type() or p.get_name() in ("ExecutePin","ExecuteContext","A","B","C")
                    srcs=[x.get_pin_path() for x in p.get_linked_source_pins()]
                    tgts=[x.get_pin_path() for x in p.get_linked_target_pins()]
                    if srcs or tgts or "Execute" in p.get_cpp_type():
                        w(f"  {p.get_name()} ({d}) <-{srcs} ->{tgts}")
                except Exception as e:
                    w(f"  pin err {str(e)[:40]}")
except Exception:
    w("\n!!!"+traceback.format_exc())
with open(OUT,"w",encoding="utf-8") as f: f.write("\n".join(lines))
unreal.log("[dump_exec] done")
