import unreal

ABP_PATH = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"

def section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

abp = unreal.load_asset(ABP_PATH)
if not abp:
    print("[ERROR] Failed to load: " + ABP_PATH)
else:
    section("기본 정보")
    print("Asset Name   : " + abp.get_name())
    print("Class        : " + abp.get_class().get_name())
    try:
        parent = abp.get_editor_property("parent_class")
        print("Parent Class : " + (parent.get_name() if parent else "N/A"))
    except Exception as e:
        print("Parent Class : (unavailable)")
    try:
        skel = abp.get_editor_property("target_skeleton")
        print("Target Skel  : " + (skel.get_path_name() if skel else "N/A"))
    except Exception as e:
        print("Target Skel  : (unavailable)")

    section("구현된 인터페이스")
    try:
        ifaces = abp.get_editor_property("implemented_interfaces")
        if ifaces:
            for iface in ifaces:
                print("- " + str(iface))
        else:
            print("(없음)")
    except Exception as e:
        print("(접근 불가: " + str(e) + ")")

    section("변수 (Blueprint Variables)")
    try:
        vars_ = abp.get_editor_property("new_variables")
        if vars_:
            for v in vars_:
                try:
                    print("- " + str(v.var_name) + " : " + str(v.var_type))
                except Exception:
                    print("- " + str(v))
        else:
            print("(없음)")
    except Exception as e:
        print("(접근 불가: " + str(e) + ")")

    section("Referenced Assets")
    try:
        ar = unreal.AssetRegistryHelpers.get_asset_registry()
        opts = unreal.AssetRegistryDependencyOptions(include_hard_package_references=True)
        deps = ar.get_dependencies(unreal.Name(ABP_PATH), opts)
        if deps:
            for d in list(deps)[:40]:
                print("- " + str(d))
            total = len(list(deps))
            if total > 40:
                print("... (total " + str(total) + ", showing top 40)")
        else:
            print("(없음)")
    except Exception as e:
        print("(조회 실패: " + str(e) + ")")

    section("Referencers (이 ABP를 쓰는 대상)")
    try:
        refs = ar.get_referencers(unreal.Name(ABP_PATH), opts)
        if refs:
            for r in list(refs)[:20]:
                print("- " + str(r))
        else:
            print("(없음)")
    except Exception as e:
        print("(조회 실패: " + str(e) + ")")

print("\n[DONE]")
