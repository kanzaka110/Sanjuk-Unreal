# -*- coding: utf-8 -*-
"""Step2: 스크래치 BP에서 GetDataTableRowFromName(와일드카드 OutRow) + BreakStruct(UDS) 검증."""
from mono import bp
import json

SCRATCH = "/Game/_WHScratch/BP_DTTest"
DIR = "/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK"

def show(tag, err, out, n=350):
    print(f"[{tag}]", "ERR" if err else "OK", out[:n])
    return err, out

# 1) 스크래치 BP 생성
err, out = show("create", *bp("create_blueprint", save_path=SCRATCH, parent_class="Actor"))
if err and "already exists" not in out:
    raise SystemExit(1)

# 2) GetDataTableRowFromName 노드 (와일드카드 OutRow)
err, out = show("getrow", *bp("add_node", asset_path=SCRATCH, graph_name="EventGraph",
                              node_type="CallFunction",
                              function_name="GetDataTableRowFromName",
                              target_class="DataTableFunctionLibrary",
                              position=[0, 0]))
if err:
    raise SystemExit(1)
getrow_id = json.loads(out).get("node_id")
print("getrow_id =", getrow_id)

# 3) BreakStruct — 유저 정의 구조체
err, out = show("break", *bp("add_node", asset_path=SCRATCH, graph_name="EventGraph",
                             node_type="BreakStruct",
                             struct_type=f"{DIR}/S_WallHandIKConfig.S_WallHandIKConfig",
                             position=[400, 0]))
if err:
    # 폴백: bare name
    err, out = show("break2", *bp("add_node", asset_path=SCRATCH, graph_name="EventGraph",
                                  node_type="BreakStruct",
                                  struct_type="S_WallHandIKConfig",
                                  position=[400, 0]))
    if err:
        raise SystemExit(1)
break_id = json.loads(out).get("node_id")
print("break_id =", break_id)

# 4) OutRow(wildcard) → Break 입력 연결 시도
err, out = show("connect", *bp("connect_pins", asset_path=SCRATCH, graph_name="EventGraph",
                               source_node=getrow_id, source_pin="OutRow",
                               target_node=break_id, target_pin="S_WallHandIKConfig"))
# 5) 노드 상세 재덤프 — OutRow 타입 해석 확인
err2, out2 = bp("get_node_details", asset_path=SCRATCH, graph_name="EventGraph", node_id=getrow_id)
print("[getrow pins]", out2[:1000])
