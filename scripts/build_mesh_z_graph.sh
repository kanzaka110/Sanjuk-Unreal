#!/bin/bash
# Build UpdateMeshOffsetZ function body via Monolith HTTP API
# Adds ~15 nodes + wiring for Mesh Z offset interpolation logic

set -e
BP="/Game/ART/Character/PC/PC_01/Blueprint/PC_01_BP"
GRAPH="UpdateMeshOffsetZ"
MCP="http://localhost:9316/mcp"
IDS_FILE="C:/Dev/Sanjuk-Unreal/scripts/mesh_z_ids.json"
echo "{}" > "$IDS_FILE"

call() {
  local ACTION=$1; local PARAMS=$2
  curl -s -X POST "$MCP" -H "Content-Type: application/json" \
    -d "{\"jsonrpc\":\"2.0\",\"method\":\"tools/call\",\"id\":1,\"params\":{\"name\":\"blueprint_query\",\"arguments\":{\"action\":\"$ACTION\",\"params\":$PARAMS}}}" \
    --max-time 20
}

# Extract node ID from response
get_id() {
  python -c "import sys,json; d=json.load(sys.stdin); t=json.loads(d['result']['content'][0]['text']); print(t.get('id',''))"
}

# Add a node, record ID under alias
add_node() {
  local ALIAS=$1; local PARAMS=$2
  local RESP=$(call "add_node" "$PARAMS")
  local ID=$(echo "$RESP" | get_id)
  if [ -z "$ID" ]; then
    echo "ERROR: $ALIAS failed to add"
    echo "$RESP" | python -c "import sys,json; d=json.load(sys.stdin); print(d['result']['content'][0]['text'][:300])"
    exit 1
  fi
  python -c "
import json
ids = json.load(open('$IDS_FILE'))
ids['$ALIAS'] = '$ID'
json.dump(ids, open('$IDS_FILE','w'))
"
  echo "  ✓ $ALIAS = $ID"
}

echo "=== 노드 생성 ==="

# 1. GetActorLocation
add_node "actor_loc" "{\"asset_path\":\"$BP\",\"graph_name\":\"$GRAPH\",\"node_type\":\"CallFunction\",\"function_name\":\"K2_GetActorLocation\",\"position\":[400,0]}"

# 2. BreakVector (current position)
add_node "break_curr" "{\"asset_path\":\"$BP\",\"graph_name\":\"$GRAPH\",\"node_type\":\"BreakStruct\",\"struct_type\":\"Vector\",\"position\":[700,0]}"

# 3. Get LastCapsuleZ
add_node "get_last_z" "{\"asset_path\":\"$BP\",\"graph_name\":\"$GRAPH\",\"node_type\":\"VariableGet\",\"variable_name\":\"LastCapsuleZ\",\"position\":[700,200]}"

# 4. DeltaZ = CurrZ - LastZ
add_node "sub_delta" "{\"asset_path\":\"$BP\",\"graph_name\":\"$GRAPH\",\"node_type\":\"CallFunction\",\"function_name\":\"Subtract_DoubleDouble\",\"position\":[1000,100]}"

# 5. Get MeshZOffset
add_node "get_offset" "{\"asset_path\":\"$BP\",\"graph_name\":\"$GRAPH\",\"node_type\":\"VariableGet\",\"variable_name\":\"MeshZOffset\",\"position\":[1000,300]}"

# 6. NewOffsetRaw = Offset - DeltaZ
add_node "sub_new_offset" "{\"asset_path\":\"$BP\",\"graph_name\":\"$GRAPH\",\"node_type\":\"CallFunction\",\"function_name\":\"Subtract_DoubleDouble\",\"position\":[1300,200]}"

# 7. Clamp(-30, 30)
add_node "clamp" "{\"asset_path\":\"$BP\",\"graph_name\":\"$GRAPH\",\"node_type\":\"CallFunction\",\"function_name\":\"FClamp\",\"position\":[1600,200]}"

# 8. FInterpTo(value, 0, dt, 18)
add_node "finterp" "{\"asset_path\":\"$BP\",\"graph_name\":\"$GRAPH\",\"node_type\":\"CallFunction\",\"function_name\":\"FInterpTo\",\"position\":[1900,200]}"

# 9. Set MeshZOffset (exec)
add_node "set_offset" "{\"asset_path\":\"$BP\",\"graph_name\":\"$GRAPH\",\"node_type\":\"VariableSet\",\"variable_name\":\"MeshZOffset\",\"position\":[2200,100]}"

# 10. Get BaseMeshZ
add_node "get_base" "{\"asset_path\":\"$BP\",\"graph_name\":\"$GRAPH\",\"node_type\":\"VariableGet\",\"variable_name\":\"BaseMeshZ\",\"position\":[2200,400]}"

# 11. BaseMeshZ + MeshZOffset_final
add_node "add_mesh_z" "{\"asset_path\":\"$BP\",\"graph_name\":\"$GRAPH\",\"node_type\":\"CallFunction\",\"function_name\":\"Add_DoubleDouble\",\"position\":[2500,350]}"

# 12. GetMesh (ACharacter)
add_node "get_mesh" "{\"asset_path\":\"$BP\",\"graph_name\":\"$GRAPH\",\"node_type\":\"CallFunction\",\"function_name\":\"GetMesh\",\"position\":[2500,550]}"

# 15. MakeVector(X, Y, newZ)
add_node "make_vec" "{\"asset_path\":\"$BP\",\"graph_name\":\"$GRAPH\",\"node_type\":\"MakeStruct\",\"struct_type\":\"Vector\",\"position\":[3400,400]}"

# 16. SetRelativeLocation (exec)
add_node "set_rel" "{\"asset_path\":\"$BP\",\"graph_name\":\"$GRAPH\",\"node_type\":\"CallFunction\",\"function_name\":\"K2_SetRelativeLocation\",\"position\":[3700,100]}"

# 17. Set LastCapsuleZ (exec)
add_node "set_last_z" "{\"asset_path\":\"$BP\",\"graph_name\":\"$GRAPH\",\"node_type\":\"VariableSet\",\"variable_name\":\"LastCapsuleZ\",\"position\":[4000,100]}"

echo
echo "=== 노드 생성 완료 ==="
cat "$IDS_FILE" | python -m json.tool
