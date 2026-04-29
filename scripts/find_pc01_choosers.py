import unreal
import json

def search_choosers():
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    filter = unreal.ARFilter(class_names=["ChooserTable"], package_paths=["/Game/Art/Character/PC/PC_01"], recursive_paths=True)
    assets = ar.get_assets(filter)
    
    results = []
    for asset in assets:
        results.append({
            "name": str(asset.asset_name),
            "path": str(asset.package_name)
        })
    return results

print("--- START CHOOSER SEARCH ---")
choosers = search_choosers()
print(json.dumps(choosers, indent=2))
print("--- END ---")
