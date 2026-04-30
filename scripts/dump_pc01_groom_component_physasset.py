"""PC_01_BP_Sanjuk의 GroomComponent.PhysicsAsset 슬롯 실측 덤프.

UE 5.7 Groom 시스템에서 PhysicsAsset이 연결될 수 있는 위치는 단 한 곳:
  UGroomComponent.PhysicsAsset (GroomComponent.h L53-55)

GroomAsset.uasset 자체와 GroomBindingAsset.uasset 자체에는 PhysicsAsset 슬롯이 없음
(GroomAsset.h, GroomBindingAsset.h grep 결과 0건 확인).

따라서 사용자가 "헤어 자체에 피직스 에셋 연결"이라고 한 것은:
  - 캐릭터 BP의 GroomComponent.PhysicsAsset 슬롯에 직접 PhysAsset asset을 꽂음
  - 또는 SkeletalMesh의 PhysicsAsset이 자동으로 인식됨
중 하나임.

이 스크립트는 PC_01_BP_Sanjuk Blueprint의 모든 GroomComponent SCS 노드를 순회해
PhysicsAsset 슬롯 실측 + CollisionComponents 등록 여부를 출력.

실행:
  UE 에디터 > Window > Developer Tools > Output Log
  Cmd 드롭다운을 'Python'으로 변경 후 입력:
    exec(open(r'C:/Dev/Sanjuk-Unreal/scripts/dump_pc01_groom_component_physasset.py').read())

결과는 Output Log + Saved/Logs/HairPhysAssetDump.txt 에 저장.
"""

from __future__ import annotations

import os
from typing import Any

import unreal

BP_PATH = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP_Sanjuk"
OUT_LOG = "HairPhysAssetDump.txt"

_LINES: list[str] = []


def log(msg: str = "") -> None:
    _LINES.append(msg)
    unreal.log(msg)


def dump_groom_component(obj: Any, idx: int) -> None:
    """GroomComponent 단일 인스턴스 덤프."""
    try:
        groom_asset = obj.get_editor_property("groom_asset")
    except Exception:
        groom_asset = None
    try:
        binding_asset = obj.get_editor_property("binding_asset")
    except Exception:
        binding_asset = None
    try:
        phys_asset = obj.get_editor_property("physics_asset")
    except Exception:
        phys_asset = None
    try:
        attachment_name = obj.get_editor_property("attachment_name")
    except Exception:
        attachment_name = "?"

    log(f"      groom_asset    = {groom_asset.get_path_name() if groom_asset else None}")
    log(f"      binding_asset  = {binding_asset.get_path_name() if binding_asset else None}")
    log(f"      physics_asset  = {phys_asset.get_path_name() if phys_asset else None}")
    log(f"      attachment     = {attachment_name}")

    # SimulationSettings (override 시 GroomAsset 값 무시 — 핵심)
    try:
        sim_settings = obj.get_editor_property("simulation_settings")
    except Exception:
        sim_settings = None
    if sim_settings:
        try:
            override = sim_settings.get_editor_property("b_override_settings")
            log(f"      sim_override        = {override}")
        except Exception as e:
            log(f"      sim_override        = [error] {e}")

        # SimulationSetup 내부 7개 핵심 필드
        sim_setup = None
        for key in ("simulation_setup", "SimulationSetup"):
            try:
                sim_setup = sim_settings.get_editor_property(key)
                if sim_setup is not None:
                    break
            except Exception:
                continue

        if sim_setup:
            _SETUP_FIELDS = (
                ("b_local_simulation",    "local_simulation"),
                ("linear_velocity_scale", "LinearVelocityScale"),
                ("angular_velocity_scale","AngularVelocityScale"),
                ("local_bone",            "LocalBone"),
                ("teleport_distance",     "TeleportDistance"),
                ("b_reset_simulation",    "reset_simulation"),
                ("b_debug_simulation",    "debug_simulation"),
            )
            for snake, fallback in _SETUP_FIELDS:
                val = None
                for k in (snake, fallback):
                    try:
                        val = sim_setup.get_editor_property(k)
                        break
                    except Exception:
                        continue
                log(f"      setup.{snake:<26}= {val}")
        else:
            log("      simulation_setup    = [추출 실패]")

        # SolverSettings (SubSteps, Iterations)
        solver = None
        for key in ("solver_settings", "SolverSettings"):
            try:
                solver = sim_settings.get_editor_property(key)
                if solver is not None:
                    break
            except Exception:
                continue
        if solver:
            for k in ("enable_simulation", "b_force_visible", "sub_steps", "iteration_count",
                      "SubSteps", "IterationCount"):
                try:
                    val = solver.get_editor_property(k)
                    log(f"      solver.{k:<27}= {val}")
                except Exception:
                    continue


def iter_cdo_components(cdo: Any) -> list[Any]:
    """CDO에서 모든 component 인스턴스 추출 (UObject reflection)."""
    components: list[Any] = []
    try:
        # 5.7: GetComponents() 또는 K2_GetComponentsByClass
        all_props = []
        for prop_name in dir(cdo):
            if prop_name.startswith("_"):
                continue
            try:
                val = getattr(cdo, prop_name, None)
                if val is None:
                    continue
                if hasattr(val, "get_class") and "Component" in val.get_class().get_name():
                    components.append((prop_name, val))
            except Exception:
                continue
        return components
    except Exception:
        return components


def dump_blueprint(bp_path: str) -> None:
    log("=" * 78)
    log(f"Blueprint: {bp_path}")
    log("=" * 78)

    bp = unreal.load_asset(bp_path)
    if bp is None:
        log(f"  [ERROR] Blueprint load failed")
        return

    log(f"  class             = {bp.get_class().get_name()}")
    gen_class = bp.generated_class() if hasattr(bp, "generated_class") else None
    log(f"  generated_class   = {gen_class.get_name() if gen_class else '?'}")

    if gen_class is None:
        log("  [ERROR] generated_class None")
        return

    cdo = unreal.get_default_object(gen_class)
    if cdo is None:
        log("  [ERROR] CDO None")
        return

    groom_components: list[tuple[str, Any]] = []

    # Method 1: SimpleConstructionScript 직접 접근 (가장 안정)
    try:
        scs = bp.get_editor_property("simple_construction_script")
        if scs:
            all_nodes = scs.get_editor_property("all_nodes")
            log(f"  [SCS] all_nodes = {len(all_nodes)}")
            for i, node in enumerate(all_nodes):
                try:
                    var_name = node.get_editor_property("variable_name")
                    template = node.get_editor_property("component_template")
                    if template is None:
                        continue
                    cls_name = template.get_class().get_name()
                    log(f"  [SCS-{i}] {var_name} = {template.get_name()} ({cls_name})")
                    if "GroomComponent" in cls_name:
                        groom_components.append((str(var_name), template))
                        dump_groom_component(template, i)
                except Exception as e:
                    log(f"  [SCS-{i}] ERROR: {e}")
        else:
            log("  [SCS] simple_construction_script None")
    except Exception as e:
        log(f"  [WARN] SCS 직접 접근 실패: {e}")

    # Method 2: SubobjectDataSubsystem + SubobjectDataBlueprintFunctionLibrary
    if not groom_components:
        try:
            subsys = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
            handles = subsys.k2_gather_subobject_data_for_blueprint(bp)
            log(f"  [SubobjectDataSubsystem] handles = {len(handles)}")

            # SubobjectData에서 객체 추출 — 5.7 API 메소드 자동 탐색
            extract_fns = []
            try:
                lib = unreal.SubobjectDataBlueprintFunctionLibrary
                for fn_name in ("get_object", "get_object_for_blueprint", "get_object_for_handle"):
                    if hasattr(lib, fn_name):
                        extract_fns.append((fn_name, getattr(lib, fn_name)))
            except Exception:
                pass
            log(f"  [SubobjectDataSubsystem] extract_fns = {[n for n, _ in extract_fns]}")

            for i, handle in enumerate(handles):
                data = subsys.k2_find_subobject_data_from_handle(handle)
                if data is None:
                    continue
                obj = None
                for fn_name, fn in extract_fns:
                    try:
                        obj = fn(data)
                        if obj is not None:
                            break
                    except Exception:
                        continue
                if obj is None:
                    # 마지막: data 자체의 attribute 들춰보기
                    for attr in ("object", "archetype", "subobject"):
                        try:
                            v = data.get_editor_property(attr)
                            if v:
                                obj = v
                                break
                        except Exception:
                            continue
                if obj is None:
                    if i == 0:
                        log(f"  [SubobjectDataSubsystem] data 메소드: {[m for m in dir(data) if not m.startswith('_')][:30]}")
                    continue
                cls_name = obj.get_class().get_name()
                comp_name = obj.get_name()
                log(f"  [SDS-{i}] {comp_name} ({cls_name})")
                if "GroomComponent" in cls_name:
                    groom_components.append((comp_name, obj))
                    dump_groom_component(obj, i)
        except Exception as e:
            log(f"  [WARN] SubobjectDataSubsystem 실패: {e}")

    # Method 3: CDO 직접 reflection (마지막 fallback — inherited 컴포넌트만 잡힘)
    if not groom_components:
        log("  [Fallback] CDO reflection으로 컴포넌트 탐색...")
        comps = iter_cdo_components(cdo)
        log(f"  [CDO] component-like properties = {len(comps)}")
        for i, (prop_name, obj) in enumerate(comps):
            cls_name = obj.get_class().get_name()
            log(f"  [CDO-{i}] {prop_name} = {obj.get_name()} ({cls_name})")
            if "GroomComponent" in cls_name:
                groom_components.append((prop_name, obj))
                dump_groom_component(obj, i)

    log("")
    log(f"  [요약] GroomComponent 발견 = {len(groom_components)}개")

    log("")
    log("[Note] GroomComponent.PhysicsAsset 우선순위 (UE 5.7 source):")
    log("  NiagaraDataInterfacePhysicsAsset.cpp L699-727:")
    log("    1. DefaultSource (Niagara DI 측 — 보통 None)")
    log("    2. attach 계층을 거슬러 올라가며 INiagaraPhysicsAssetDICollectorInterface 캐스트")
    log("       → GroomComponent::BuildAndCollect (L3699) 도달")
    log("       → CollisionComponents의 PhysAsset들 + GroomComponent.PhysicsAsset 반환")
    log("    3. attach된 SkeletalMesh 발견 시 SourceComponent로 사용")
    log("       → GroomComponent.PhysicsAsset 있으면 그걸로, 없으면 SkelMesh.PhysicsAsset로 fallback")


def main() -> None:
    dump_blueprint(BP_PATH)

    project_dir = unreal.SystemLibrary.get_project_directory()
    out_path = os.path.join(project_dir, "Saved", "Logs", OUT_LOG)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(_LINES))
    log("")
    log(f"[saved] {out_path}")


main()
