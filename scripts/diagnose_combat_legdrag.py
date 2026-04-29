"""PC_01 전투 시 다리 밀림 종합 진단 덤프.

목적:
  1) IK Layer AnimGraph 안에 ControlRig (FootClamp) 노드가 있는지 + 어떤 변수에 바인딩되는지
  2) FootClamp Rig의 Angle_Clamp_Pitch/Roll/Yaw default 현재값
  3) ABP의 전투 관련 변수(IsGuarding/IsLockOn/IsFullBodySlotActive/OverlayPoseState/
     FootIKWeight/FootPlacementAlpha) default + 갱신 함수 후보
  4) IK Layer LinkedAnimLayer 입력 핀(FootPlacementAlpha 등)이 ABP 어디서 오는지 단서

실행:
  UE 에디터 > Output Log > Cmd=Python
  exec(open(r'C:/Dev/Sanjuk-Unreal/scripts/diagnose_combat_legdrag.py').read())

산출:
  Output Log + Saved/Logs/CombatLegDragDiagnose.txt
"""
from __future__ import annotations

import os
from typing import Any

import unreal

ABP_PATH = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
ABP_GEN = f"{ABP_PATH}.PC_01_ABP_C"
IK_LAYER_PATH = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK"
IK_LAYER_GEN = f"{IK_LAYER_PATH}.PC_01_AnimLayer_IK_C"
FOOTCLAMP_PATH = "/Game/ART/Character/PC/PC_01/Rig/PC_01_CtrlRig_FootClamp"
FOOTCLAMP_GEN = f"{FOOTCLAMP_PATH}.PC_01_CtrlRig_FootClamp_C"

_LINES: list[str] = []


def log(msg: str = "") -> None:
    _LINES.append(msg)
    unreal.log(msg)


def section(title: str) -> None:
    log("")
    log("=" * 78)
    log(title)
    log("=" * 78)


def safe(fn, default: str = "(err)") -> Any:
    try:
        return fn()
    except Exception as e:
        return f"{default}: {type(e).__name__}: {str(e)[:80]}"


def load_class(path: str):
    for loader in (unreal.load_class, unreal.load_object):
        try:
            obj = loader(None, path)
            if obj is not None:
                return obj
        except Exception:
            continue
    return None


def cdo_of(class_path: str):
    cls = load_class(class_path)
    if cls is None:
        return None
    try:
        return unreal.get_default_object(cls)
    except Exception:
        return None


def list_inner_objects(asset, kw_filter: list[str]) -> dict[str, list[str]]:
    """asset 패키지 내부 객체 중 키워드 매칭 클래스 분류."""
    found: dict[str, list[str]] = {}
    try:
        package = asset.get_outermost()
        inner = unreal.find_objects_with_outer(package)
        for obj in inner:
            cls_name = obj.get_class().get_name()
            if any(kw.lower() in cls_name.lower() for kw in kw_filter):
                found.setdefault(cls_name, []).append(obj.get_name())
    except Exception as e:
        log(f"  inner enumerate err: {type(e).__name__}: {str(e)[:80]}")
    return found


# ============================================================
# Part 1: IK Layer AnimGraph 노드 (ControlRig 포함 여부)
# ============================================================
def part1_ik_layer_graph() -> None:
    section("Part 1) PC_01_AnimLayer_IK AnimGraph 노드 스캔")

    asset = unreal.load_asset(IK_LAYER_PATH)
    if not asset:
        log("[FAIL] IK Layer 로드 실패")
        return

    KW = [
        "AnimGraphNode", "AnimNode",
        "ControlRig", "FootPlacement", "LegIK",
        "ModifyBone", "TwoBoneIK", "FullBodyIK",
        "ApplyAdditive", "Layered", "Slot",
        "BlendList", "LinkedAnim", "Cached",
        "Inertialization", "DeadBlending",
    ]
    found = list_inner_objects(asset, KW)
    if not found:
        log("(분류된 노드 없음)")
        return
    for cls_name in sorted(found.keys()):
        names = found[cls_name]
        log(f"  {cls_name} x {len(names)}")
        for n in names[:8]:
            log(f"    - {n}")
        if len(names) > 8:
            log(f"    ... (+{len(names)-8})")

    # ControlRig 노드 상세
    section("Part 1b) ControlRig 노드 상세 (FootClamp 호출 위치 추정)")
    try:
        package = asset.get_outermost()
        inner = unreal.find_objects_with_outer(package)
        for obj in inner:
            cls = obj.get_class().get_name()
            if "ControlRig" not in cls and "AnimGraphNode" not in cls:
                continue
            if "ControlRig" not in cls:
                continue
            log(f"\n  [{cls}] {obj.get_name()}")
            # 주요 프로퍼티 덤프
            for prop in ("control_rig_class", "ControlRigClass",
                         "alpha", "alpha_input_type", "alpha_scale_bias",
                         "alpha_bool_name", "alpha_curve_name"):
                v = safe(lambda p=prop, o=obj: o.get_editor_property(p),
                         default="(no prop)")
                log(f"      {prop} = {v}")
            # node 안의 FAnimNode_ControlRig struct 시도
            for node_prop in ("node",):
                v = safe(lambda p=node_prop, o=obj: o.get_editor_property(p),
                         default="(no node)")
                log(f"      {node_prop} = {v}")
                if v and not str(v).startswith("("):
                    for sub in ("control_rig_class", "alpha", "alpha_input_type",
                                "alpha_bool_name", "alpha_curve_name",
                                "input_settings", "output_settings"):
                        sv = safe(lambda s=sub, val=v: val.get_editor_property(s),
                                  default="-")
                        log(f"        .{sub} = {sv}")
    except Exception as e:
        log(f"  err: {type(e).__name__}: {str(e)[:120]}")


# ============================================================
# Part 2: FootClamp Rig 변수 default
# ============================================================
def part2_footclamp_defaults() -> None:
    section("Part 2) PC_01_CtrlRig_FootClamp 변수 default 실측")

    cdo = cdo_of(FOOTCLAMP_GEN)
    if cdo is None:
        # ControlRigBlueprint은 generated class 경로가 다를 수 있음
        bp = unreal.load_asset(FOOTCLAMP_PATH)
        if bp:
            try:
                gen = bp.get_editor_property("generated_class")
                if gen:
                    cdo = unreal.get_default_object(gen)
            except Exception:
                pass
    if cdo is None:
        log("[FAIL] FootClamp CDO 접근 불가")
        return

    log(f"  CDO = {cdo}")
    for var in ("BoneNames", "Angle_Clamp_Pitch", "Angle_Clamp_Roll",
                "Angle_Clamp_Yaw"):
        v = safe(lambda x=var: cdo.get_editor_property(x), default="(missing)")
        log(f"  {var} = {v}")


# ============================================================
# Part 3: ABP 전투 관련 변수 default + 갱신 함수 추적
# ============================================================
def part3_combat_vars() -> None:
    section("Part 3) PC_01_ABP 전투 관련 변수 default")

    cdo = cdo_of(ABP_GEN)
    if cdo is None:
        log("[FAIL] ABP CDO 접근 불가")
        return

    TARGETS = [
        "IsGuarding", "IsLockOn", "PrevIsLockOn",
        "IsFullBodySlotActive", "PrevIsFullBodySlotActive",
        "OverlayPoseState", "PrevOverlayPoseState",
        "OverlayWeight",
        "FootIKWeight", "CurrentFootIKWeight", "FootPlacementAlpha",
        "FullBodySlotWeight", "PrevFullBodySlotWeight",
        "AnimStance", "PrevAnimStance",
        "MovementState", "MovementMode",
    ]
    for var in TARGETS:
        v = safe(lambda x=var: cdo.get_editor_property(x), default="(missing)")
        log(f"  {var} = {v}")


# ============================================================
# Part 4: 갱신 함수 그래프 — UpdateVariables, GetFootIKWeight,
#           BlueprintThreadSafeUpdateAnimation 노드 분석
# ============================================================
def part4_update_paths() -> None:
    section("Part 4) ABP UpdateVariables / GetFootIKWeight / "
            "BlueprintThreadSafeUpdateAnimation 노드 추출")

    abp = unreal.load_asset(ABP_PATH)
    if not abp:
        log("[FAIL]")
        return

    target_funcs = [
        "UpdateVariables", "GetFootIKWeight",
        "BlueprintThreadSafeUpdateAnimation",
        "GetFootPlacementPlantSettings",
        "GetFootPlacementInterpolationSettings",
        "OnStateEntry_PlayingMontage",
    ]

    try:
        bel = unreal.BlueprintEditorLibrary
        graphs = bel.get_all_graphs(abp)
        if not graphs:
            log("(no graphs)")
            return
        for g in graphs:
            gname = safe(lambda gg=g: gg.get_name(), default="?")
            if str(gname) not in target_funcs:
                continue
            log(f"\n  --- Graph: {gname} ---")
            try:
                nodes = bel.get_nodes(g)
                for n in nodes[:60]:
                    ncls = safe(lambda nn=n: nn.get_class().get_name(),
                                default="?")
                    nname = safe(lambda nn=n: nn.get_name(), default="?")
                    title = ""
                    try:
                        title = str(n.get_node_title(0))[:80]
                    except Exception:
                        try:
                            title = str(n.get_node_title())[:80]
                        except Exception:
                            pass
                    log(f"    {ncls}  [{nname}]  {title}")
                if len(nodes) > 60:
                    log(f"    ... (+{len(nodes)-60})")
            except Exception as e:
                log(f"    (nodes err: {str(e)[:80]})")
    except Exception as e:
        log(f"  err: {type(e).__name__}: {str(e)[:120]}")


# ============================================================
# Part 5: ABP InterpolationSettings / PlantSettings default 덤프
#          (FootPlacement이 다리 밀림에 영향을 주는 핵심 파라미터)
# ============================================================
def part5_plant_interp_settings() -> None:
    section("Part 5) ABP PlantSettings / InterpolationSettings default")
    cdo = cdo_of(ABP_GEN)
    if cdo is None:
        log("[FAIL]")
        return
    for var in ("PlantSettingsDefault", "PlantSettingsStop",
                "PlantSettingsFullBody",
                "InterpolationSettingsDefault", "InterpolationSettingsStops",
                "InterpolationSettingsFullBody"):
        v = safe(lambda x=var: cdo.get_editor_property(x), default="(missing)")
        # struct → export_text
        try:
            txt = v.export_text()
            log(f"\n  [{var}]")
            for chunk in txt.replace("),", ")\n").split("\n"):
                log(f"    {chunk}")
        except Exception:
            log(f"  {var} = {v}")


def main() -> None:
    log(f"START — PC_01 전투 다리 밀림 진단")
    log(f"ABP_PATH      = {ABP_PATH}")
    log(f"IK_LAYER_PATH = {IK_LAYER_PATH}")
    log(f"FOOTCLAMP     = {FOOTCLAMP_PATH}")

    part1_ik_layer_graph()
    part2_footclamp_defaults()
    part3_combat_vars()
    part4_update_paths()
    part5_plant_interp_settings()

    out_dir = unreal.Paths.project_saved_dir() + "Logs"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "CombatLegDragDiagnose.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(_LINES))
    log("")
    log(f"=> 저장됨: {out_path}")


main()
