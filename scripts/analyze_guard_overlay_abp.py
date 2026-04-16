"""
PC_01_Fist_Normal_Guard_Overlay_ABP 구조 분석 스크립트
UE5 에디터 Python 콘솔에서 실행

사용법:
  1. 에디터 → 출력 로그(Output Log) → 하단 드롭다운 → Python 선택
  2. 이 스크립트 전체를 붙여넣기
  3. 결과를 복사하여 공유
"""
import unreal

# --- 설정 ---
TARGET_NAME = "PC_01_Fist_Normal_Guard_Overlay_ABP"
SEARCH_PATHS = [
    "/Game/ART/Character/PC/PC_01/OverlaySystem/",
    "/Game/ART/Character/PC/PC_01/",
    "/Game/ART/Character/PC/",
    "/Game/",
]


def section(title: str) -> None:
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def find_asset(name: str) -> str | None:
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    for base in SEARCH_PATHS:
        try:
            assets = ar.get_assets_by_path(base, recursive=True)
            for a in assets:
                if name.lower() in str(a.asset_name).lower():
                    pkg = str(a.package_name)
                    print(f"[FOUND] {a.asset_name} @ {pkg}")
                    print(f"  Class: {a.asset_class_path.asset_name}")
                    return pkg
        except Exception:
            continue
    return None


def print_abp_info(pkg_path: str) -> None:
    asset = unreal.load_asset(pkg_path)
    if asset is None:
        print(f"[ERROR] load_asset failed: {pkg_path}")
        return

    section("기본 정보")
    print(f"Name: {asset.get_name()}")
    print(f"Class: {asset.get_class().get_name()}")

    # 부모 클래스
    try:
        parent = asset.get_editor_property("parent_class")
        if parent:
            print(f"Parent Class: {parent.get_name()}")
    except Exception:
        pass

    # 스켈레톤
    try:
        skeleton = asset.get_editor_property("target_skeleton")
        if skeleton:
            print(f"Skeleton: {skeleton.get_path_name()}")
    except Exception:
        pass

    # 인터페이스
    section("구현된 인터페이스 (Implemented Interfaces)")
    try:
        ifaces = asset.get_editor_property("implemented_interfaces")
        if ifaces and len(ifaces) > 0:
            for iface in ifaces:
                print(f"  - {iface.get_editor_property('interface').get_name()}")
        else:
            print("  (없음)")
    except Exception as e:
        print(f"  조회 실패: {str(e)[:80]}")

    # AnimGraph 그래프 목록
    section("그래프 목록 (Graphs)")
    try:
        from unreal import AnimationBlueprintLibrary
        graphs = unreal.BlueprintEditorLibrary.get_graphs(asset)
        if graphs:
            for g in graphs:
                print(f"  - {g.get_name()} (Schema: {g.get_schema().get_name() if g.get_schema() else 'None'})")
        else:
            print("  (BlueprintEditorLibrary 미지원)")
    except Exception:
        print("  (그래프 열거 미지원 — 에디터에서 직접 확인 필요)")

    # 변수 목록
    section("변수 (Variables)")
    try:
        variables = unreal.BlueprintEditorLibrary.get_variables(asset)
        if variables:
            for v in variables:
                print(f"  - {v}")
        else:
            print("  (BlueprintEditorLibrary 미지원)")
    except Exception:
        try:
            # fallback: CDO 프로퍼티 스캔
            cdo = unreal.get_default_object(asset.generated_class())
            if cdo:
                for prop_name in dir(cdo):
                    if not prop_name.startswith("_"):
                        try:
                            val = cdo.get_editor_property(prop_name)
                            if val is not None:
                                print(f"  - {prop_name}: {val}")
                        except Exception:
                            pass
        except Exception:
            print("  (변수 열거 실패 — 에디터에서 직접 확인 필요)")

    # 함수/이벤트 목록
    section("함수 / 이벤트")
    try:
        funcs = unreal.BlueprintEditorLibrary.get_functions(asset)
        if funcs:
            for f in funcs:
                print(f"  - {f}")
    except Exception:
        print("  (함수 열거 미지원)")

    # 애님 레이어
    section("Linked Anim Layers")
    try:
        from unreal import AnimationBlueprintLibrary as ABL
        layers = ABL.get_linked_anim_layers(asset)
        if layers:
            for layer in layers:
                print(f"  - {layer}")
        else:
            print("  (없거나 API 미지원)")
    except Exception:
        print("  (API 미지원 — 에디터에서 직접 확인 필요)")

    # 레퍼런스 (참조하는 에셋)
    section("참조 에셋 (Dependencies)")
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    try:
        deps = ar.get_dependencies(pkg_path)
        anim_deps = [
            d for d in deps
            if any(
                kw in str(d).lower()
                for kw in [
                    "anim", "montage", "blend", "motion",
                    "pose", "chooser", "database", "guard",
                    "overlay", "fist",
                ]
            )
        ]
        if anim_deps:
            for d in sorted(set(str(x) for x in anim_deps)):
                print(f"  - {d}")
        else:
            print("  (애니메이션 관련 참조 없음 — 전체 출력)")
            for d in list(deps)[:30]:
                print(f"  - {d}")
            if len(deps) > 30:
                print(f"  ... (+{len(deps) - 30} more)")
    except Exception as e:
        print(f"  참조 조회 실패: {str(e)[:80]}")


# --- 실행 ---
section(f"에셋 검색: {TARGET_NAME}")
found_path = find_asset(TARGET_NAME)

if found_path:
    print_abp_info(found_path)
else:
    print(f"\n[NOT FOUND] '{TARGET_NAME}'을 찾지 못했습니다.")
    print("OverlaySystem 폴더 전체 에셋을 나열합니다:\n")
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    for base in SEARCH_PATHS[:2]:
        try:
            assets = ar.get_assets_by_path(base, recursive=True)
            if assets:
                print(f"\n[{base}]")
                for a in list(assets)[:40]:
                    print(f"  - {a.asset_name} ({a.asset_class_path.asset_name})")
                if len(list(assets)) > 40:
                    print(f"  ... (+{len(list(assets)) - 40} more)")
        except Exception:
            pass

print("\n[DONE]")
