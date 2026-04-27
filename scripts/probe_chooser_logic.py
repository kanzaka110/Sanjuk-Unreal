import unreal
import json

def dump_chooser_logic(path):
    chooser = unreal.load_object(None, path)
    if not chooser: return "Fail"
    
    data = {"path": path, "columns": [], "rows": []}
    
    # 컬럼(조건 변수) 확인
    try:
        cols = chooser.get_editor_property("ColumnsStructs")
        for col in cols:
            # 컬럼이 참조하는 프로퍼티 이름 추출 (예: IsLockOn, TargetRotationDelta 등)
            data["columns"].append(str(col))
    except: pass
    
    # 행(Row)별 조건 및 에셋 확인
    # (참고: Chooser API는 버전에 따라 접근 방식이 상이하므로 리플렉션 활용)
    return data

PATH = "/Game/Art/Character/PC/PC_01/StateMachine/GroundMoving.GroundMoving"
print("--- CHOOSER LOGIC DUMP ---")
print(dump_chooser_logic(PATH))
print("--- END ---")
