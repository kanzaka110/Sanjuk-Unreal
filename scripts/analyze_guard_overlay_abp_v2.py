"""
PC_01_Fist_Normal_Guard_Overlay_ABP 심층 분석 v2
참조 에셋 + 노드 구조 + 변수 추출
"""
import unreal

PKG = "/Game/ART/Character/PC/PC_01/OverlaySystem/Poses/Fist_Normal_Guard/PC_01_Fist_Normal_Guard_Overlay_ABP"
ar = unreal.AssetRegistryHelpers.get_asset_registry()


def section(title: str) -> None:
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


# 1. 참조 에셋 (Dependencies)
section("참조 에셋 (Dependencies)")
try:
    opts = unreal.AssetRegistryDependencyOptions()
    opts.include_hard = True
    opts.include_soft = True
    deps = ar.get_dependencies(PKG, opts)
    if deps:
        for d in sorted(set(str(x) for x in deps)):
            print(f"  {d}")
    else:
        print("  (없음)")
except Exception as e:
    print(f"  실패: {str(e)[:120]}")

# 2. 이 에셋을 참조하는 에셋 (Referencers)
section("이 ABP를 참조하는 에셋 (Referencers)")
try:
    opts2 = unreal.AssetRegistryDependencyOptions()
    opts2.include_hard = True
    opts2.include_soft = True
    refs = ar.get_referencers(PKG, opts2)
    if refs:
        for r in sorted(set(str(x) for x in refs)):
            print(f"  {r}")
    else:
        print("  (없음)")
except Exception as e:
    print(f"  실패: {str(e)[:120]}")

# 3. ABP 로드 후 Generated Class 프로퍼티 스캔
section("AnimInstance CDO 프로퍼티 (커스텀 변수)")
try:
    abp = unreal.load_asset(PKG)
    gen_class = abp.get_editor_property("generated_class")
    if gen_class:
        cdo = unreal.get_default_object(gen_class)
        skip_prefixes = (
            "on_montage", "on_all_montage", "root_motion",
            "notify_queue", "active_animation",
        )
        skip_exact = {
            "delta_time", "current_proxy",
        }
        props = []
        for attr in sorted(dir(cdo)):
            if attr.startswith("_"):
                continue
            if attr.startswith(skip_prefixes):
                continue
            if attr in skip_exact:
                continue
            try:
                val = cdo.get_editor_property(attr)
                props.append((attr, val))
            except Exception:
                pass
        if props:
            for name, val in props:
                vtype = type(val).__name__
                print(f"  {name}: {val}  ({vtype})")
        else:
            print("  (커스텀 프로퍼티 없음)")
except Exception as e:
    print(f"  실패: {str(e)[:120]}")

# 4. 같은 폴더의 에셋 목록
section("같은 폴더 에셋 (/OverlaySystem/Poses/Fist_Normal_Guard/)")
try:
    folder = "/Game/ART/Character/PC/PC_01/OverlaySystem/Poses/Fist_Normal_Guard/"
    assets = ar.get_assets_by_path(folder, recursive=True)
    if assets:
        for a in assets:
            print(f"  {a.asset_name} ({a.asset_class_path.asset_name})")
    else:
        print("  (비어있음)")
except Exception as e:
    print(f"  실패: {str(e)[:80]}")

# 5. OverlaySystem 전체 폴더 구조
section("OverlaySystem 전체 에셋 목록")
try:
    base = "/Game/ART/Character/PC/PC_01/OverlaySystem/"
    assets = ar.get_assets_by_path(base, recursive=True)
    if assets:
        grouped = {}
        for a in assets:
            folder_key = str(a.package_path)
            if folder_key not in grouped:
                grouped[folder_key] = []
            grouped[folder_key].append(
                f"{a.asset_name} ({a.asset_class_path.asset_name})"
            )
        for folder_key in sorted(grouped.keys()):
            print(f"\n  [{folder_key}]")
            for item in sorted(grouped[folder_key]):
                print(f"    {item}")
    else:
        print("  (비어있음)")
except Exception as e:
    print(f"  실패: {str(e)[:80]}")

# 6. MotionMatching 폴더에서 Guard 관련 에셋
section("MotionMatching 폴더 — Guard 관련")
try:
    mm_base = "/Game/ART/Character/PC/PC_01/MotionMatching/"
    assets = ar.get_assets_by_path(mm_base, recursive=True)
    if assets:
        guard_assets = [
            a for a in assets
            if any(
                kw in str(a.asset_name).lower()
                for kw in ["guard", "fist", "overlay", "combat", "block", "defend"]
            )
        ]
        if guard_assets:
            for a in guard_assets:
                print(f"  {a.asset_name} ({a.asset_class_path.asset_name})")
                print(f"    @ {a.package_name}")
        else:
            print("  Guard 관련 에셋 없음. 전체 목록 (최대 30개):")
            for a in list(assets)[:30]:
                print(f"  {a.asset_name} ({a.asset_class_path.asset_name})")
            if len(list(assets)) > 30:
                print(f"  ... (+{len(list(assets)) - 30} more)")
    else:
        print("  (비어있음)")
except Exception as e:
    print(f"  실패: {str(e)[:80]}")

# 7. 부모 클래스 체인
section("부모 클래스 체인")
try:
    abp = unreal.load_asset(PKG)
    gen_class = abp.get_editor_property("generated_class")
    cls = gen_class
    chain = []
    while cls:
        chain.append(cls.get_name())
        cls = cls.get_super_class()
    for i, c in enumerate(chain):
        indent = "  " * i
        print(f"  {indent}└ {c}")
except Exception as e:
    print(f"  실패: {str(e)[:120]}")

print("\n[DONE]")
