import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/diag_idle_l.txt"
L=[]
try:
    # 1) 런타임: 현재 손 자세 vs 기대값
    w = unreal.UnrealEditorSubsystem().get_game_world()
    p = unreal.GameplayStatics.get_player_pawn(w, 0)
    mesh = p.get_component_by_class(unreal.SkeletalMeshComponent)
    ai = mesh.get_anim_instance()
    g = ai.get_editor_property
    L.append(f"alpha={float(g('WallHandAlpha')):.2f} bR={bool(g('bWallHandRight'))} bF={bool(g('bWallHandFront'))}")
    qh = mesh.get_socket_quaternion("hand_l")
    qc = mesh.get_world_transform().rotation  # 컴포넌트 월드 회전
    def conj(q): return unreal.Quat(-q.x,-q.y,-q.z,q.w)
    qh_comp = conj(qc).multiply(qh)
    L.append(f"hand_l comp-space=({qh_comp.x:.4f},{qh_comp.y:.4f},{qh_comp.z:.4f},{qh_comp.w:.4f})")
    L.append(f"기대 offL      =(0.5078,-0.4921,0.5078,0.4921)")
    exp = unreal.Quat(0.507812,-0.492064,0.507812,0.492064)
    d = abs(qh_comp.x*exp.x+qh_comp.y*exp.y+qh_comp.z*exp.z+qh_comp.w*exp.w)
    import math
    L.append(f"기대와 각도차 = {math.degrees(2*math.acos(min(d,1.0))):.1f}도")
    # 2) CR 배선: QSelL/QMulL/Effector
    bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK")
    ctrl = bp.get_controller_by_name("RigVMModel")
    gg = ctrl.get_graph()
    nodes = {n.get_name(): n for n in gg.get_nodes()}
    L.append(f"QSelL 존재={'QSelL' in nodes} QMulL 존재={'QMulL' in nodes}")
    if "QSelL" in nodes:
        for pin in nodes["QSelL"].get_pins():
            nm=pin.get_name()
            if nm in ("Condition","IfTrue","IfFalse","Result"):
                srcs=[s.get_pin_path() for s in pin.get_linked_source_pins()]
                tgts=[t.get_pin_path() for t in pin.get_linked_target_pins()]
                dv=""
                try: dv=pin.get_default_value()[:80]
                except Exception: pass
                L.append(f"  QSelL.{nm} src={srcs} tgt={tgts} def={dv}")
    if "TwoBoneIK_L" in nodes:
        for pin in nodes["TwoBoneIK_L"].get_pins():
            if pin.get_name()=="Effector":
                for sp in pin.get_sub_pins():
                    if sp.get_name()=="Rotation":
                        L.append(f"  Effector.Rotation src={[s.get_pin_path() for s in sp.get_linked_source_pins()]}")
except Exception:
    L.append(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
