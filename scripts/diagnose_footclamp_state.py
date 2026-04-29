"""PC_01 FootClamp 종합 진단 스크립트.

출력 항목:
1. PC_01_AnimLayer_IK AnimGraph 노드 순서 + ControlRig 노드 위치 (FootClamp 호출처)
2. PC_01_CtrlRig_FootClamp 변수 default (BoneNames, Angle_Clamp_*)
3. Clamp 노드 X/Y/Z pin link source (Roll/Pitch 스왑 유지 여부)
4. SetTransform 노드의 bPropagateToChildren / Translation/Scale 처리 모드

UE 5.7.4 SB2 커스텀에서 실행. UE 에디터 Python Output Log에서 결과 확인.
"""

from __future__ import annotations

import unreal


IK_LAYER_PATH = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK"
FOOTCLAMP_PATH = "/Game/ART/Character/PC/PC_01/Rig/PC_01_CtrlRig_FootClamp"

LINE = "=" * 70


def section(title: str) -> None:
    print("\n" + LINE)
    print(title)
    print(LINE)


def safe(fn, default: str = ""):
    try:
        return fn()
    except Exception as e:
        return f"(err: {str(e)[:120]})"


def get_objects_with_outer(outer):
    """Replacement for unreal.find_objects_with_outer (not present in this UE 5.7 build).

    Walks the AssetRegistry/EditorAssetLibrary scope and falls back to scanning
    via unreal.load_object on known sub-paths if needed.
    """
    results = []
    try:
        ar = unreal.AssetRegistryHelpers.get_asset_registry()
        outer_path = outer.get_path_name()
        # Sub-objects of a UPackage live as <package>.<name>
        # We use AssetRegistry.get_assets_by_package_name when applicable
        try:
            pkg_name = outer_path.split(".")[0]
            assets = ar.get_assets_by_package_name(pkg_name)
            for ad in assets:
                obj = ad.get_asset()
                if obj:
                    results.append(obj)
        except Exception:
            pass
    except Exception:
        pass

    # Fallback: enumerate via gc-style listing
    try:
        # unreal.PythonScriptLibrary or low-level enumeration may differ per build.
        # Try transient package walk.
        for obj in unreal.SystemLibrary.get_outer_objects(outer) if hasattr(unreal.SystemLibrary, "get_outer_objects") else []:
            if obj not in results:
                results.append(obj)
    except Exception:
        pass

    return results


# ----------------------------------------------------------------------------
# 1. AnimLayer_IK 의 AnimGraph 노드 순서 (T3D export 기반)
# ----------------------------------------------------------------------------

section("[1] PC_01_AnimLayer_IK AnimGraph 노드 (T3D export)")

ik_layer = unreal.load_asset(IK_LAYER_PATH)
if not ik_layer:
    print("[ERROR] AnimLayer_IK not found")
else:
    print(f"Loaded: {ik_layer.get_name()}, class={ik_layer.get_class().get_name()}")
    # Find AnimGraph object
    package = ik_layer.get_outermost()
    inner = get_objects_with_outer(package)
    print(f"Inner objects: {len(inner)}")

    # AnimGraph 노드만 추출
    anim_nodes = []
    for obj in inner:
        cls = obj.get_class().get_name()
        if cls.startswith("AnimGraphNode_"):
            try:
                pos_x = obj.get_editor_property("node_pos_x")
                pos_y = obj.get_editor_property("node_pos_y")
            except Exception:
                pos_x = pos_y = -9999
            try:
                comment = obj.get_editor_property("node_comment") or ""
            except Exception:
                comment = ""
            anim_nodes.append((pos_x, pos_y, cls, obj.get_name(), comment))

    anim_nodes.sort(key=lambda t: (t[0], t[1]))
    print(f"\nAnimGraphNode count: {len(anim_nodes)}")
    print(f"{'X':>6} {'Y':>6}  {'Class':<48}  Name")
    print("-" * 110)
    for pos_x, pos_y, cls, name, comment in anim_nodes:
        suffix = f"  // {comment}" if comment else ""
        print(f"{pos_x:>6} {pos_y:>6}  {cls:<48}  {name}{suffix}")

    # ControlRig 노드만 별도 강조 (FootClamp / LookAt 등)
    section("[1b] ControlRig AnimGraphNode 상세 (Animation Class / 호출 ControlRig)")
    for obj in inner:
        cls = obj.get_class().get_name()
        if "ControlRig" in cls and cls.startswith("AnimGraphNode_"):
            print(f"\n--- {obj.get_name()} ({cls}) ---")
            # AnimNode property
            try:
                node = obj.get_editor_property("node")
                print(f"node: {node}")
                for pname in [
                    "control_rig_class",
                    "ControlRigClass",
                    "control_rig",
                    "alpha",
                    "alpha_input_type",
                    "bExecute",
                ]:
                    try:
                        v = node.get_editor_property(pname)
                        print(f"  node.{pname} = {v}")
                    except Exception:
                        pass
            except Exception as e:
                print(f"node err: {str(e)[:100]}")
            # Direct property scan for ControlRigClass
            for pname in [
                "control_rig_class",
                "ControlRigClass",
                "control_rig",
            ]:
                try:
                    v = obj.get_editor_property(pname)
                    print(f"  {pname} = {v}")
                except Exception:
                    pass


# ----------------------------------------------------------------------------
# 2. FootClamp 변수 default
# ----------------------------------------------------------------------------

section("[2] PC_01_CtrlRig_FootClamp 변수 default")

footclamp = unreal.load_asset(FOOTCLAMP_PATH)
if not footclamp:
    print("[ERROR] FootClamp not found")
else:
    print(f"Loaded: {footclamp.get_name()}, class={footclamp.get_class().get_name()}")

    # ControlRig 변수 = ControlRigBlueprint.public_graph_function_headers / variables
    # 또는 generated class CDO 의 properties
    cdo = None
    try:
        gen_class = footclamp.get_editor_property("generated_class") or footclamp.generated_class()
        cdo = unreal.get_default_object(gen_class)
        print(f"CDO: {cdo}")
    except Exception as e:
        print(f"CDO load err: {str(e)[:100]}")

    # 변수 목록 (RigVMBlueprint API)
    print("\n--- Member variables (variables 또는 new_variables) ---")
    for prop_name in ["variables", "new_variables", "member_variables"]:
        try:
            v = footclamp.get_editor_property(prop_name)
            if v:
                print(f"\n{prop_name}: {v}")
                if hasattr(v, "__iter__"):
                    for item in v:
                        try:
                            print(f"  - {item}")
                        except Exception:
                            pass
        except Exception:
            pass

    # CDO 에서 직접 읽기
    if cdo:
        print("\n--- CDO property dump (관심 변수) ---")
        candidate_names = [
            "BoneNames",
            "Bone_Names",
            "Angle_Clamp_Roll",
            "Angle_Clamp_Pitch",
            "Angle_Clamp_Yaw",
            "AngleClampRoll",
            "AngleClampPitch",
            "AngleClampYaw",
            "Clamp_Roll",
            "Clamp_Pitch",
            "Clamp_Yaw",
            "Min_Roll",
            "Max_Roll",
            "Min_Pitch",
            "Max_Pitch",
            "Min_Yaw",
            "Max_Yaw",
        ]
        for n in candidate_names:
            try:
                v = cdo.get_editor_property(n)
                print(f"  {n} = {v}")
            except Exception:
                pass

    # RigVMBlueprint Controller로 변수 정의 + 디폴트 추출
    print("\n--- RigVMController 변수 정의 ---")
    try:
        ctrl = footclamp.get_controller_by_name("RigVMModel")
        if ctrl:
            print(f"Controller: {ctrl}")
            try:
                graph = ctrl.get_graph()
                print(f"Graph: {graph.get_name() if graph else None}")
            except Exception as e:
                print(f"get_graph err: {str(e)[:100]}")
    except Exception as e:
        print(f"controller err: {str(e)[:100]}")


# ----------------------------------------------------------------------------
# 3. Clamp / SetTransform 노드 pin link 분석 (T3D 스타일)
# ----------------------------------------------------------------------------

section("[3] FootClamp 내부 RigVM 노드 + pin link (Clamp 축 매핑 검증)")

if footclamp:
    package = footclamp.get_outermost()
    rig_inner = get_objects_with_outer(package)

    # RigVMNode 추출
    rigvm_nodes = []
    rigvm_pins = []
    rigvm_links = []
    for obj in rig_inner:
        cls = obj.get_class().get_name()
        if "RigVM" in cls and (
            "Node" in cls or "UnitNode" in cls or "VariableNode" in cls
        ):
            rigvm_nodes.append((cls, obj))
        if cls in ("RigVMPin",):
            rigvm_pins.append(obj)
        if cls in ("RigVMLink",):
            rigvm_links.append(obj)

    print(f"RigVMNode count: {len(rigvm_nodes)}")
    print(f"RigVMPin count: {len(rigvm_pins)}")
    print(f"RigVMLink count: {len(rigvm_links)}")

    # 노드 분류 + 변수 노드는 referenced_variable 출력
    print("\n--- Nodes ---")
    for cls, obj in rigvm_nodes:
        name = obj.get_name()
        info_parts = [f"{cls} :: {name}"]
        # VariableNode → which variable
        for pname in [
            "referenced_variable",
            "variable_name",
            "variable",
            "variable_description",
        ]:
            try:
                v = obj.get_editor_property(pname)
                if v not in (None, "", "None"):
                    info_parts.append(f"{pname}={v}")
            except Exception:
                pass
        # UnitNode → script struct
        for pname in [
            "script_struct",
            "scriptstruct_path",
            "method_name",
            "function_name",
        ]:
            try:
                v = obj.get_editor_property(pname)
                if v not in (None, "", "None"):
                    info_parts.append(f"{pname}={v}")
            except Exception:
                pass
        print("  " + " | ".join(str(p) for p in info_parts))

    # Clamp 노드의 pin 링크 추적: Pin이 outer로 가지는 노드 이름 + 링크의 source/target
    print("\n--- Clamp_1 / Set Transform 관련 pin 링크 ---")
    for link in rigvm_links:
        try:
            src = link.get_editor_property("source_pin")
            tgt = link.get_editor_property("target_pin")
            src_path = src.get_path_name() if src else "(none)"
            tgt_path = tgt.get_path_name() if tgt else "(none)"
            if any(
                kw in (src_path + tgt_path)
                for kw in [
                    "Clamp",
                    "SetTransform",
                    "BoneNames",
                    "Variable",
                    "QuaternionToEuler",
                    "QuaternionFromEuler",
                ]
            ):
                print(f"  {src_path}\n    -> {tgt_path}")
        except Exception as e:
            pass


print("\n[DONE]")
