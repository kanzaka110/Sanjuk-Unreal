"""④ STAGE 0 probe: GunModeAim/FootClamp CR 구조 + 팔 본 축 데이터 산출.
실행: Monolith editor_query run_console_command  ->  py "<this>"
결과: 아래 OUT 파일로 직접 write (UE 로그 회수 불안정 회피).
"""
import unreal

OUT = r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\wallhand_cr_probe.txt"
GUN = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_GunModeAim"
FOOT = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_FootClamp"

lines = []
def w(s): lines.append(str(s))


def dump_cr(path, label, max_nodes=80):
    w("\n" + "=" * 50)
    w(f"[{label}] {path}")
    bp = unreal.load_asset(path)
    if bp is None:
        w("  LOAD FAILED"); return
    w(f"  class={bp.get_class().get_name()}")
    # 1) 멤버 변수 (anim 노드 핀으로 노출되는 입력)
    try:
        nv = bp.get_editor_property("new_variables")
        w(f"  new_variables ({len(nv)}):")
        for v in nv:
            try:
                vn = v.get_editor_property("var_name")
                pt = v.get_editor_property("var_type")
                w(f"    - {vn} : {pt.pin_category} / {pt.pin_sub_category_object}")
            except Exception as e:
                w(f"    - <var introspect err {str(e)[:60]}>")
    except Exception as e:
        w(f"  new_variables err: {str(e)[:80]}")
    # 2) 컨트롤러/그래프 노드
    try:
        ctrl = bp.get_controller_by_name("RigVMModel")
        graph = ctrl.get_graph()
        nodes = graph.get_nodes()
        w(f"  graph nodes ({len(nodes)}):")
        for n in nodes[:max_nodes]:
            np = n.get_node_path()
            ss = ""
            try:
                s = n.get_script_struct()
                if s: ss = s.get_name()
            except Exception:
                pass
            w(f"    - {np}  [{n.get_class().get_name()}]  {ss}")
        if len(nodes) > max_nodes:
            w(f"    ... (+{len(nodes)-max_nodes} more)")
    except Exception as e:
        w(f"  controller/graph err: {str(e)[:120]}")
    # 3) local variables
    try:
        ctrl = bp.get_controller_by_name("RigVMModel")
        lv = ctrl.get_graph().get_local_variables()
        w(f"  local_variables ({len(lv)}):")
        for v in lv:
            w(f"    - {v}")
    except Exception as e:
        w(f"  local_variables err: {str(e)[:80]}")


def arm_axes(path):
    w("\n" + "=" * 50)
    w(f"[ARM AXES from hierarchy initial-global] {path}")
    bp = unreal.load_asset(path)
    try:
        hier = bp.get_hierarchy()
    except Exception as e:
        w(f"  get_hierarchy err: {str(e)[:80]}"); return

    def gt(bone):
        key = unreal.RigElementKey(type=unreal.RigElementType.BONE, name=bone)
        try:
            return hier.get_global_transform(key, initial=True)
        except Exception as e:
            return None

    for side in ("l", "r"):
        ua = gt(f"upperarm_{side}")
        la = gt(f"lowerarm_{side}")
        ha = gt(f"hand_{side}")
        if not (ua and la and ha):
            w(f"  side {side}: missing bone(s) ua={ua is not None} la={la is not None} ha={ha is not None}")
            continue
        ua_loc = ua.translation; la_loc = la.translation; ha_loc = ha.translation
        # primary axis (upperarm->lowerarm) in upperarm local space
        dirw = (la_loc - ua_loc)
        prim_local = ua.transform_vector_no_scale(dirw) if hasattr(ua, "transform_vector_no_scale") else None
        # fallback: inverse transform direction
        inv = ua.inverse()
        prim_local2 = inv.transform_vector(dirw)
        prim_local2 = prim_local2.normal() if hasattr(prim_local2, "normal") else prim_local2
        # bend plane normal (cross of UA->LA and LA->HA) for pole/secondary
        v1 = (la_loc - ua_loc).normal()
        v2 = (ha_loc - la_loc).normal()
        w(f"  --- {side} ---")
        w(f"    upperarm_{side} pos={ua_loc}")
        w(f"    lowerarm_{side} pos={la_loc}")
        w(f"    hand_{side}     pos={ha_loc}")
        w(f"    PRIMARY(UA->LA) in UA-local (norm) = {prim_local2}")
        w(f"    seg1 dir(world)={v1}  seg2 dir(world)={v2}")


dump_cr(GUN, "GUN MODE AIM")
dump_cr(FOOT, "FOOT CLAMP")
arm_axes(FOOT)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
unreal.log(f"[wallhand_probe] WROTE {OUT}")
