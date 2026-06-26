# -*- coding: utf-8 -*-
"""
WallHandIK 최종 설정 스냅샷 / 복원 스크립트 (2026-06-26)
==========================================================
PC_01 벽 짚기 손 IK 의 ControlRig + ABP 최종 튜닝값 일괄 적용.

배경: CR(PC_01_CtrlRig_WallHandIK) 은 미저장 상태에서 리로드되면 churn 으로
      핀값/링크가 디스크 옛버전으로 되돌아간다. 이 스크립트는 노드를 새로 만들지
      않고(이미 존재 전제), 최종 "값"만 재적용하고 save_packages 로 저장한다.

⚠ 저장은 반드시 EditorLoadingAndSavingUtils.save_packages([pkg], False) 사용.
   EditorAssetLibrary.save_asset() 는 에디터가 에셋을 열고 있으면 False 반환(이번 세션 내내 실패).

에디터 Python 콘솔(또는 Monolith editor_query "py <path>")에서 실행.

== 아키텍처 요약 (6/26 최종) ==
[Primary 팜 조준]  PalmAim(R)/PalmAim_1(L), Kind=Direction, palm-out 축을
   SecAxisLerp_2(R)/SecAxisLerp_3(L) 로 블렌드. Target=PalmReachLerp(붙음=벽방향 reachN, 멀어짐=down(0,0,-1)).
[Secondary 롤]     Kind=Location, Weight=1, Axis 를 SecAxisLerp(R)/SecAxisLerp_1(L) 로 블렌드.
[블렌드 driver]    ReachBlend = Remap(|ReachSub|, 40~60cm -> 0~1).  (리치 거리 기반: 붙음=A, 뻗음=B)
                   * alpha 는 dist<=45 에서 1로 포화 -> 붙음/뻗음 구분 불가라 리치거리 사용.
[팔꿈치 pole]      TwoBoneIK PoleVector, PoleVectorSpace=root(액터상대). 아래+바깥.
                   root 축 실측: root+X=액터좌측, root+Y=액터전방, root+Z=up. 측면축=root.X.
[스파인 lean]      MulK.A<-WallHandSpineLean, B=0.5. 분배 spine_02/03/neck/head.
                   머리 정면 고정: 합(spine)= -(neck+head). Off_*.Weight=1.0 상수(=alpha 격리, 팝 방지).
[ABP 릴리스]       SetSmoothedWallHandAlpha SelectFloat A(release)=5, B(attach)=10. (낮을수록 부드럽게)
                   bWallHandRight 는 no-hit 시 홀드(side 스왑 팝 방지).
"""
import unreal, traceback

CR = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
LOG = []
def w(s): LOG.append(str(s));
def _set(ctrl, pin, val):
    try: w(f"set {pin}={val} -> {ctrl.set_pin_default_value(pin, val)}")
    except Exception as e: w(f"set {pin} ERR {str(e)[:70]}")

def apply_cr():
    bp = unreal.load_asset(CR)
    ctrl = bp.get_controller_by_name("RigVMModel")
    # --- Palm Primary: Direction, palm-out 축 블렌드 ---
    _set(ctrl, "PalmAim.Primary.Kind", "Direction")
    _set(ctrl, "PalmAim_1.Primary.Kind", "Direction")
    # SecAxisLerp_2 (R primary axis): A=붙음(palm-out +Y), B=뻗음
    for p,v in [("SecAxisLerp_2.A.X","0.0"),("SecAxisLerp_2.A.Y","1.0"),("SecAxisLerp_2.A.Z","0.0"),
                ("SecAxisLerp_2.B.X","-1.0"),("SecAxisLerp_2.B.Y","0.0"),("SecAxisLerp_2.B.Z","0.0")]:
        _set(ctrl,p,v)
    # SecAxisLerp_3 (L primary axis): R 의 미러(negate X,Y)
    for p,v in [("SecAxisLerp_3.A.X","0.0"),("SecAxisLerp_3.A.Y","-1.0"),("SecAxisLerp_3.A.Z","0.0"),
                ("SecAxisLerp_3.B.X","1.0"),("SecAxisLerp_3.B.Y","0.0"),("SecAxisLerp_3.B.Z","0.0")]:
        _set(ctrl,p,v)
    # --- Palm Secondary: Location, Weight 1, 축 블렌드 ---
    _set(ctrl, "PalmAim.Secondary.Kind", "Location")
    _set(ctrl, "PalmAim_1.Secondary.Kind", "Location")
    _set(ctrl, "PalmAim.Secondary.Weight", "1.0")
    _set(ctrl, "PalmAim_1.Secondary.Weight", "1.0")
    # SecAxisLerp (R secondary axis)
    for p,v in [("SecAxisLerp.A.X","1.0"),("SecAxisLerp.A.Y","0.0"),("SecAxisLerp.A.Z","0.0"),
                ("SecAxisLerp.B.X","0.0"),("SecAxisLerp.B.Y","1.0"),("SecAxisLerp.B.Z","0.0")]:
        _set(ctrl,p,v)
    # SecAxisLerp_1 (L secondary axis): R 의 미러
    for p,v in [("SecAxisLerp_1.A.X","-1.0"),("SecAxisLerp_1.A.Y","0.0"),("SecAxisLerp_1.A.Z","0.0"),
                ("SecAxisLerp_1.B.X","0.0"),("SecAxisLerp_1.B.Y","-1.0"),("SecAxisLerp_1.B.Z","0.0")]:
        _set(ctrl,p,v)
    # --- ReachBlend (리치거리 driver) ---
    for p,v in [("ReachBlend.SourceMinimum","40.0"),("ReachBlend.SourceMaximum","60.0"),
                ("ReachBlend.TargetMinimum","0.0"),("ReachBlend.TargetMaximum","1.0"),("ReachBlend.bClamp","true")]:
        _set(ctrl,p,v)
    # --- 팔꿈치 pole (root 공간, 아래+바깥) ---
    for p,v in [("TwoBoneIK_R.PoleVector.X","-1.0"),("TwoBoneIK_R.PoleVector.Y","0.0"),("TwoBoneIK_R.PoleVector.Z","-1.0"),
                ("TwoBoneIK_R.PoleVectorSpace",'(Type=Bone,Name="root")'),
                ("TwoBoneIK_L.PoleVector.X","1.0"),("TwoBoneIK_L.PoleVector.Y","0.0"),("TwoBoneIK_L.PoleVector.Z","-1.0"),
                ("TwoBoneIK_L.PoleVectorSpace",'(Type=Bone,Name="root")')]:
        _set(ctrl,p,v)
    # --- 스파인 lean 분배 + 머리 카운터 + Off weight 상수 ---
    for p,v in [("MulK.B","0.5"),
                ("Mul_spine_02.B","0.4"),("Mul_spine_03.B","0.8"),
                ("Mul_neck_02.B","-0.5"),("Mul_head.B","-0.7"),
                ("Off_spine_02.Weight","1.0"),("Off_spine_03.Weight","1.0"),
                ("Off_neck_02.Weight","1.0"),("Off_head.Weight","1.0")]:
        _set(ctrl,p,v)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); w("CR compiled")
    pkg = bp.get_package()
    w("CR save_packages -> " + str(unreal.EditorLoadingAndSavingUtils.save_packages([pkg], False)))

if __name__ == "__main__":
    try: apply_cr()
    except Exception: w(traceback.format_exc())
    print("\n".join(LOG))
    unreal.log("[wallhand_config_20260626] done")
