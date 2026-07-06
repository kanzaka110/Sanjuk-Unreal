# -*- coding: utf-8 -*-
"""
WallHandIK CR 전체 상태 덤프 (재사용 가능)
==========================================
PC_01_CtrlRig_WallHandIK 의 멤버변수 / 노드+핀 디폴트 / 링크 전체를 텍스트로 덤프.
에디터 Python 콘솔 또는 Monolith editor_query run_console_command "py <이 파일>" 로 실행.
출력: OUT 경로 텍스트 파일 (unreal.log 회수는 불안정 — 파일 출력이 표준).
"""
import unreal, traceback, os, datetime

CR = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260706_dt/cr_dump_0706.txt"

L = []
def w(s):
    L.append(str(s))

def dump_pin(p, depth=1):
    try:
        ind = "  " * depth
        d = ""
        try:
            d = p.get_default_value()
        except Exception:
            pass
        try:
            direc = str(p.get_direction()).split(".")[-1]
        except Exception:
            direc = "?"
        line = f"{ind}{p.get_name()} [{direc}]"
        if d:
            line += f" = {d}"
        w(line)
        try:
            subs = p.get_sub_pins()
        except Exception:
            subs = []
        # 서브핀 디폴트는 부모 default 에 합쳐 나오므로 링크 있는 서브핀만 추가 표기
        for sp in subs:
            try:
                if sp.get_linked_source_pins() or sp.get_linked_target_pins():
                    w(f"{ind}  {sp.get_name()} (linked)")
            except Exception:
                pass
    except Exception as e:
        w(f"  pin ERR {str(e)[:80]}")

try:
    w(f"# CR dump {datetime.datetime.now().isoformat()} asset={CR}")
    bp = unreal.load_asset(CR)
    w(f"loaded: {bp}")

    w("\n=== MEMBER VARIABLES ===")
    try:
        for v in bp.get_member_variables():
            w(f"  {v}")
    except Exception as e:
        w(f"  vars ERR {str(e)[:120]}")

    ctrl = bp.get_controller_by_name("RigVMModel")
    g = ctrl.get_graph()

    w("\n=== NODES (pins + defaults) ===")
    for n in g.get_nodes():
        try:
            title = ""
            try:
                title = n.get_node_title()
            except Exception:
                pass
            w(f"\n[{n.get_name()}] {title}")
            for p in n.get_pins():
                dump_pin(p)
        except Exception as e:
            w(f"node ERR {str(e)[:100]}")

    w("\n=== LINKS ===")
    links_done = False
    try:
        for lk in g.get_links():
            try:
                w(f"  {lk.get_source_pin().get_pin_path()} -> {lk.get_target_pin().get_pin_path()}")
            except Exception:
                w(f"  link {lk}")
        links_done = True
    except Exception as e:
        w(f"  get_links ERR {str(e)[:100]} — 핀 기반 폴백")
    if not links_done:
        for n in g.get_nodes():
            for p in n.get_pins():
                try:
                    for src in p.get_linked_source_pins():
                        w(f"  {src.get_pin_path()} -> {p.get_pin_path()}")
                except Exception:
                    pass

except Exception:
    w(traceback.format_exc())

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(L))
unreal.log(f"[dump_wallhand_cr] done -> {OUT} ({len(L)} lines)")
