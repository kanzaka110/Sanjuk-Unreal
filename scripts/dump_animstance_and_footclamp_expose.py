"""PC_01 ABP/IK Layer/FootClamp 진단 dump.

Inspector 역할: AnimStance enum 정확한 정의 + LinkedAnimLayer 매핑 + ControlRig
노드 expose 핀 + FootClamp 변수 default 값을 한 번에 dump.

Run inside Unreal Editor (Python Output Log):
    exec(open("C:/Dev/Sanjuk-Unreal/scripts/dump_animstance_and_footclamp_expose.py").read())

Outputs to: {Project}/Saved/Logs/AnimStanceFootClampDump.txt
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any

import unreal

ABP_PATH = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
IK_LAYER_PATH = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK"
RIG_PATH = "/Game/ART/Character/PC/PC_01/Rig/PC_01_CtrlRig_FootClamp"

OUT_DIR = Path("E:/Perforce/SB2/Workspace/Internal/SB2/Saved/Logs")
TS = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
OUT_FILE = OUT_DIR / f"AnimStanceFootClampDump_{TS}.txt"

LINES: list[str] = []


def emit(s: str = "") -> None:
    print(s)
    LINES.append(s)


def section(title: str) -> None:
    emit("")
    emit("=" * 70)
    emit(title)
    emit("=" * 70)


def safe(fn, default: Any = "(err)") -> Any:
    try:
        return fn()
    except Exception as e:
        return f"(err: {type(e).__name__}: {str(e)[:80]})"


# =============================================================
# A. AnimStance enum 정확 정의
# =============================================================
section("A. AnimStance / PrevAnimStance enum 정의 추적")

abp = unreal.load_asset(ABP_PATH)
if not abp:
    emit("[ERR] ABP load fail")
    raise SystemExit

abp_class = abp.generated_class()
emit(f"ABP loaded: {abp.get_name()}  class={abp_class.get_name() if abp_class else '?'}")

cdo = unreal.get_default_object(abp_class) if abp_class else None
emit(f"CDO: {cdo}")

# enum 추적: AnimStance variable의 underlying enum
# ABP variable list -> 'byte' 표시되지만 실제는 BP-level UByteProperty(Enum=...)
# Blueprint reflection: get_blueprint_variable_type
try:
    from unreal import BlueprintEditorLibrary as BEL
    # 직접 Property 접근
    found_enum = None
    if cdo:
        for prop_name in ("AnimStance", "PrevAnimStance", "MovementState",
                          "MovementMode", "OverlayPoseState"):
            try:
                v = cdo.get_editor_property(prop_name)
                emit(f"  CDO.{prop_name} = {v!r}  type={type(v).__name__}")
            except Exception as e:
                emit(f"  CDO.{prop_name} err: {str(e)[:80]}")
except Exception as e:
    emit(f"BEL err: {e}")

# 핵심: BPVariableDescription에서 실제 enum 클래스 찾기
emit("\n-- BlueprintGeneratedClass 변수 디스크립션 --")
try:
    bp_class = abp.generated_class()
    # NewVariables 배열에서 AnimStance 검색
    for var_name in ("AnimStance", "PrevAnimStance", "MovementState",
                     "OverlayPoseState", "MoveSide", "WriggleMoveType",
                     "MovementMode", "PendingWalkMode"):
        try:
            prop = bp_class.find_property(unreal.Name(var_name))
            if prop:
                emit(f"  {var_name}: {prop} class={type(prop).__name__}")
            else:
                emit(f"  {var_name}: not found via find_property")
        except Exception as e:
            emit(f"  {var_name} err: {str(e)[:80]}")
except Exception as e:
    emit(f"reflection err: {e}")

# BP source: get_blueprint_function_class 등
emit("\n-- ABP 변수 타입 reflection (from blueprint) --")
try:
    # Blueprint object 자체 (UBlueprint)
    bp = abp  # AnimBlueprint inherits UBlueprint
    # NewVariables는 TArray<FBPVariableDescription>
    new_vars = safe(lambda: bp.get_editor_property("new_variables"), [])
    if new_vars and hasattr(new_vars, "__iter__"):
        match_names = ("AnimStance", "PrevAnimStance", "MovementState",
                       "OverlayPoseState", "MoveSide", "WriggleMoveType")
        for vd in new_vars:
            try:
                vname = str(safe(lambda: vd.var_name))
                if vname in match_names:
                    var_type = safe(lambda: vd.var_type)
                    pin_cat = safe(lambda: var_type.pin_category)
                    pin_sub = safe(lambda: var_type.pin_sub_category)
                    pin_subobj = safe(lambda: var_type.pin_sub_category_object)
                    emit(f"  [{vname}]")
                    emit(f"    pin_category    = {pin_cat}")
                    emit(f"    pin_sub_category= {pin_sub}")
                    emit(f"    sub_obj         = {pin_subobj}")
                    if pin_subobj and hasattr(pin_subobj, "get_path_name"):
                        emit(f"    sub_obj_path    = {pin_subobj.get_path_name()}")
            except Exception as e:
                emit(f"  vd err: {str(e)[:80]}")
    else:
        emit("  new_variables not iterable")
except Exception as e:
    emit(f"new_variables err: {e}")

# 만약 enum 경로를 잡았으면 enum entries 덤프
emit("\n-- enum entries (if AnimStance enum 발견 시) --")
try:
    bp = abp
    new_vars = bp.get_editor_property("new_variables")
    target_enum = None
    for vd in new_vars:
        try:
            if str(vd.var_name) == "AnimStance":
                obj = vd.var_type.pin_sub_category_object
                if obj:
                    target_enum = obj
                    break
        except Exception:
            continue
    if target_enum:
        emit(f"  AnimStance enum class: {target_enum.get_path_name()}")
        # UEnum API
        try:
            num = target_enum.num_enums()
            emit(f"  num_enums={num} (마지막은 _MAX)")
            for i in range(num):
                name = target_enum.get_name_by_index(i)
                disp = safe(lambda i=i: target_enum.get_display_name_text_by_index(i))
                val = safe(lambda i=i: target_enum.get_value_by_index(i))
                emit(f"    [{i}]  value={val}  name={name}  display={disp}")
        except Exception as e:
            emit(f"  enum iter err: {e}")
    else:
        emit("  AnimStance enum 객체를 못 잡음 (BP reflection 한계)")
except Exception as e:
    emit(f"enum dump err: {e}")


# =============================================================
# B. ABP -> IK Layer LinkedAnimLayer expose 핀
# =============================================================
section("B. PC_01_ABP AnimGraph -> LinkedAnimLayer (IK) 노드 expose 상태")

# AnimGraph 의 LinkedAnimLayer 노드 찾기 -> connected_pins 출력 (ABP 본체 쪽)
# Monolith로 이미 알고 있는 정보를 보강하기 위해 T3D를 export
try:
    # AnimGraphSchema export — 그냥 패키지 내에서 LinkedAnimLayer 노드 찾기
    pkg = abp.get_outermost()
    inner = unreal.find_objects_with_outer(pkg)
    layer_nodes = []
    for obj in inner:
        cls = obj.get_class().get_name()
        if "LinkedAnimLayer" in cls:
            layer_nodes.append(obj)
    emit(f"LinkedAnimLayer 노드 총 {len(layer_nodes)}개")
    for n in layer_nodes:
        emit(f"\n  -- {n.get_name()} (class={n.get_class().get_name()}) --")
        # AnimGraphNode_LinkedAnimLayer 의 InterfaceFunctionName / Layer / Tag 등
        for prop in ("layer", "interface", "tag", "instance_class"):
            v = safe(lambda p=prop: n.get_editor_property(p))
            emit(f"    {prop} = {v}")
        # 핀 목록 (노출된 변수 포함)
        try:
            # AnimGraphNode 는 UEdGraphNode 상속 -> Pins 배열
            pins = safe(lambda: n.get_editor_property("pins"), [])
            if pins:
                emit(f"    Pins ({len(pins)}):")
                for p in pins:
                    pname = safe(lambda p=p: p.pin_name)
                    pdir = safe(lambda p=p: p.direction)
                    ptype = safe(lambda p=p: p.pin_type)
                    pcat = safe(lambda pt=ptype: pt.pin_category)
                    psub = safe(lambda pt=ptype: pt.pin_sub_category_object)
                    emit(f"      {pdir} {pname} : {pcat}"
                         f"{' / ' + str(psub.get_name()) if psub else ''}")
        except Exception as e:
            emit(f"    pins err: {str(e)[:80]}")
except Exception as e:
    emit(f"layer node enum err: {e}")


# =============================================================
# C. IK Layer 내부 — ControlRig 노드의 expose 핀
# =============================================================
section("C. PC_01_AnimLayer_IK 내부 ControlRig 노드 expose 상태")

ik = unreal.load_asset(IK_LAYER_PATH)
if not ik:
    emit("[ERR] IK Layer load fail")
else:
    emit(f"IK Layer loaded: {ik.get_name()}")
    pkg = ik.get_outermost()
    inner = unreal.find_objects_with_outer(pkg)

    # AnimGraphNode_ControlRig 노드들
    cr_nodes = []
    fp_nodes = []
    legik_nodes = []
    other_anim_nodes = []
    for obj in inner:
        cls = obj.get_class().get_name()
        if cls == "AnimGraphNode_ControlRig":
            cr_nodes.append(obj)
        elif "FootPlacement" in cls:
            fp_nodes.append(obj)
        elif "LegIK" in cls:
            legik_nodes.append(obj)
        elif cls.startswith("AnimGraphNode_"):
            other_anim_nodes.append(obj)

    emit(f"\nAnimGraphNode_ControlRig: {len(cr_nodes)}")
    emit(f"AnimGraphNode_FootPlacement: {len(fp_nodes)}")
    emit(f"AnimGraphNode_LegIK: {len(legik_nodes)}")
    emit(f"기타 AnimGraphNode: {len(other_anim_nodes)}")
    for n in other_anim_nodes:
        emit(f"  - {n.get_class().get_name()}::{n.get_name()}")

    for n in cr_nodes:
        emit(f"\n  ControlRig node: {n.get_name()}")
        # node position
        x = safe(lambda: n.get_editor_property("node_pos_x"))
        y = safe(lambda: n.get_editor_property("node_pos_y"))
        emit(f"    pos = ({x}, {y})")
        # ControlRig class
        for prop in ("control_rig_class", "rig_class", "control_rig",
                     "alpha", "alpha_input_type"):
            v = safe(lambda p=prop: n.get_editor_property(p))
            emit(f"    {prop} = {v}")
        # 핀 dump
        try:
            pins = safe(lambda: n.get_editor_property("pins"), [])
            if pins:
                emit(f"    Pins ({len(pins)}):")
                for p in pins:
                    pname = str(safe(lambda p=p: p.pin_name))
                    pdir = str(safe(lambda p=p: p.direction))
                    pdef = safe(lambda p=p: p.default_value)
                    plinks = safe(lambda p=p: len(p.linked_to))
                    emit(f"      {pdir:7s} {pname:50s}  links={plinks}"
                         f"  default={str(pdef)[:40]}")
        except Exception as e:
            emit(f"    pins err: {str(e)[:80]}")

    # FootPlacement 노드도 위치 확인 (X 좌표 비교용)
    for n in fp_nodes:
        emit(f"\n  FootPlacement node: {n.get_name()}")
        x = safe(lambda: n.get_editor_property("node_pos_x"))
        y = safe(lambda: n.get_editor_property("node_pos_y"))
        emit(f"    pos = ({x}, {y})")


# =============================================================
# D. FootClamp Rig 변수 default + 정의
# =============================================================
section("D. PC_01_CtrlRig_FootClamp 변수 default")

rig = unreal.load_asset(RIG_PATH)
if not rig:
    emit("[ERR] Rig load fail")
else:
    emit(f"Rig loaded: {rig.get_name()}")
    # ControlRigBlueprint API
    # public variables 접근
    try:
        # CR variables는 보통 controller.get_external_variables() 또는
        # blueprint의 variables 배열로
        for getter in ("get_default_model", "get_focused_model", "get_model"):
            try:
                fn = getattr(rig, getter, None)
                if not callable(fn):
                    continue
                m = fn()
                if not m:
                    continue
                ctrl = rig.get_or_create_controller(m)
                if not ctrl:
                    continue
                emit(f"  controller: {ctrl}")
                # external variables
                try:
                    ev = rig.get_external_variables()
                    emit(f"  external_variables: {len(ev) if ev else 0}")
                    for e in (ev or []):
                        emit(f"    - {e.name}: type={e.type_name}"
                             f" default={e.default_value}")
                except Exception as ex:
                    emit(f"  external err: {str(ex)[:80]}")
                # blueprint variables
                try:
                    bv = rig.get_local_variables()
                    if bv:
                        emit(f"  local_variables: {len(bv)}")
                        for v in bv:
                            emit(f"    - {v}")
                except Exception:
                    pass
                break
            except Exception:
                continue
    except Exception as e:
        emit(f"rig vars err: {e}")

    # 변수 default 값을 Python으로 직접 (CDO 트릭)
    try:
        rig_class = rig.generated_class()
        if rig_class:
            rig_cdo = unreal.get_default_object(rig_class)
            emit(f"\n  CDO: {rig_cdo}")
            for vname in ("BoneNames", "Angle_Clamp_Pitch", "Angle_Clamp_Roll",
                          "Angle_Clamp_Yaw"):
                v = safe(lambda n=vname: rig_cdo.get_editor_property(n))
                emit(f"    CDO.{vname} = {v}")
    except Exception as e:
        emit(f"  CDO err: {e}")


# =============================================================
# E. ABP CDO에서 PelvisSettings / IK 관련 default 추가 확인
# =============================================================
section("E. ABP CDO — PelvisSettings 및 IK 관련 default")

if cdo:
    for vname in ("PelvisSettingsDefault", "PelvisSettingsMove",
                  "PelvisSettingsProne", "FootPlacementAlpha"):
        try:
            v = cdo.get_editor_property(vname)
            # struct는 export_text로 짧게
            if hasattr(v, "export_text"):
                emit(f"  {vname}: {v.export_text()[:200]}")
            else:
                emit(f"  {vname}: {v}")
        except Exception as e:
            emit(f"  {vname} err: {str(e)[:60]}")


# =============================================================
# F. IK Layer CDO — PelvisSettings 4개 default
# =============================================================
section("F. IK Layer CDO — PelvisSettings 4개 default + bUseFootIK 등")

if ik:
    ik_class = ik.generated_class() if hasattr(ik, "generated_class") else None
    ik_cdo = unreal.get_default_object(ik_class) if ik_class else None
    if ik_cdo:
        for vname in ("PelvisSettingsDefault", "PelvisSettingsMove",
                      "PelvisSettingsProne", "PelvisSettingsTraversal",
                      "bUseFootIK", "Body_LookAtSettings",
                      "Head_LookAtSettings"):
            try:
                v = ik_cdo.get_editor_property(vname)
                if hasattr(v, "export_text"):
                    emit(f"  {vname}: {v.export_text()[:300]}")
                else:
                    emit(f"  {vname}: {v}")
            except Exception as e:
                emit(f"  {vname} err: {str(e)[:60]}")
    else:
        emit("  IK CDO 못 잡음")


# =============================================================
# 끝 — 파일로 저장
# =============================================================
section("DONE — write to file")

try:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text("\n".join(LINES), encoding="utf-8")
    emit(f"\nWrote: {OUT_FILE}")
except Exception as e:
    emit(f"write err: {e}")

print(f"\n[DONE] {OUT_FILE}")
