import unreal
import json

def dump_chooser(path):
    ct = unreal.load_object(None, path)
    if not ct: return {"error": "Load fail"}
    
    columns = ct.get_editor_property("ColumnsStructs")
    col_names = []
    for col in columns:
        # FChooserParameterProxy에서 실제 변수 이름 추출 시도
        try:
            exp = col.export_text()
            col_names.append(exp)
        except:
            col_names.append(str(col))
            
    results = ct.get_editor_property("ResultsStructs")
    row_data = []
    for res in results:
        try:
            row_data.append(res.export_text())
        except:
            row_data.append(str(res))
            
    return {"columns": col_names, "rows": row_data}

PATH = "/Game/Art/Character/PC/PC_01/StateMachine/GroundIdle"
print("--- DUMP ---")
print(json.dumps(dump_chooser(PATH), indent=2))
print("--- END ---")
