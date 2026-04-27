import unreal
import json

def get_chooser_info(path):
    chooser = unreal.load_object(None, path)
    if not chooser:
        return f"Failed to load Chooser: {path}"
    
    results = {
        "path": path,
        "rows": []
    }
    
    # Chooser 테이블의 행(Row) 정보를 수동으로 파싱하거나 속성에서 추출
    # Chooser SDK의 버전에 따라 접근 방식이 다를 수 있음
    try:
        # 일반적인 Chooser 데이터 구조 (v0.12 기준)
        rows = chooser.get_editor_property("Rows")
        for i, row in enumerate(rows):
            row_data = {
                "index": i,
                "asset": str(row.get_editor_property("ResultAsset")) if hasattr(row, "ResultAsset") else "Unknown"
            }
            results["rows"].append(row_data)
    except Exception as e:
        results["error"] = str(e)
        
    return results

def get_abp_info(path):
    abp = unreal.load_object(None, path)
    if not abp:
        return f"Failed to load ABP: {path}"
    
    results = {
        "path": path,
        "skeleton": str(abp.target_skeleton.get_name()),
        "layers": []
    }
    
    # 애니메이션 레이어 인터페이스 정보 추출
    try:
        # Blueprint 내부의 가상 함수/레이어 확인
        for func in abp.blueprint_generated_class.get_editor_property("FunctionData"):
            results["layers"].append(str(func.get_name()))
    except:
        pass
        
    return results

# 타겟 경로 설정
CHOOSER_PATH = "/Game/Art/Character/PC/PC_01/StateMachine/GroundMoving.GroundMoving"
ABP_PATH = "/Game/Art/Character/PC/PC_01/PC_01_ABP.PC_01_ABP"

print("--- START PROBE ---")
print("CHOOSER DATA:")
print(json.dumps(get_chooser_info(CHOOSER_PATH), indent=2))
print("\nABP DATA:")
print(json.dumps(get_abp_info(ABP_PATH), indent=2))
print("--- END PROBE ---")
