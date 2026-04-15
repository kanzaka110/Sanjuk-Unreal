"""Build all connections for UpdateMeshOffsetZ function."""
import json, subprocess, sys

BP = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_BP"
GRAPH = "UpdateMeshOffsetZ"
MCP = "http://localhost:9316/mcp"

ids = json.load(open("C:/Dev/Sanjuk-Unreal/scripts/mesh_z_ids.json"))


def call(action: str, params: dict) -> dict:
    payload = {
        "jsonrpc": "2.0", "method": "tools/call", "id": 1,
        "params": {"name": "blueprint_query",
                   "arguments": {"action": action, "params": params}}
    }
    r = subprocess.run(
        ["curl", "-s", "-X", "POST", MCP,
         "-H", "Content-Type: application/json",
         "-d", json.dumps(payload)],
        capture_output=True, text=True, timeout=20)
    d = json.loads(r.stdout)
    txt = d["result"]["content"][0]["text"]
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return {"_raw": txt}


def connect(src_alias: str, src_pin: str, dst_alias: str, dst_pin: str) -> None:
    src = ids[src_alias]
    dst = ids[dst_alias]
    res = call("connect_pins", {
        "asset_path": BP, "graph_name": GRAPH,
        "source_node": src, "source_pin": src_pin,
        "target_node": dst, "target_pin": dst_pin})
    ok = res.get("success", False)
    mark = "✓" if ok else "✗"
    print(f"  {mark} {src_alias}.{src_pin} → {dst_alias}.{dst_pin}"
          f"{'' if ok else '  ' + str(res)[:150]}")


def set_default(alias: str, pin: str, value: str) -> None:
    nid = ids[alias]
    res = call("set_pin_default", {
        "asset_path": BP, "graph_name": GRAPH,
        "node_id": nid, "pin_name": pin, "value": value})
    ok = res.get("success", False)
    mark = "✓" if ok else "✗"
    print(f"  {mark} set {alias}.{pin} = {value}"
          f"{'' if ok else '  ' + str(res)[:150]}")


print("=== 데이터 연결 ===")
# DeltaZ 계산
connect("actor_loc",      "ReturnValue",  "break_curr",     "Vector")
connect("break_curr",     "Z",            "sub_delta",      "A")
connect("get_last_z",     "LastCapsuleZ", "sub_delta",      "B")

# NewOffsetRaw = Offset - DeltaZ
connect("get_offset",     "MeshZOffset",  "sub_new_offset", "A")
connect("sub_delta",      "ReturnValue",  "sub_new_offset", "B")

# Clamp
connect("sub_new_offset", "ReturnValue",  "clamp",          "Value")

# FInterpTo
connect("clamp",          "ReturnValue",  "finterp",        "Current")
connect("entry",          "DeltaSeconds", "finterp",        "DeltaTime")

# Set MeshZOffset
connect("finterp",        "ReturnValue",  "set_offset",     "MeshZOffset")

# BaseMeshZ + FinalOffset
connect("get_base",       "BaseMeshZ",    "add_mesh_z",     "A")
connect("finterp",        "ReturnValue",  "add_mesh_z",     "B")

# MakeVector (X, Y default 0, Z = add result)
connect("add_mesh_z",     "ReturnValue",  "make_vec",       "Z")

# SetRelativeLocation
connect("get_mesh",       "Mesh",         "set_rel",        "self")
connect("make_vec",       "Vector",       "set_rel",        "NewLocation")

# LastCapsuleZ = CurrZ
connect("break_curr",     "Z",            "set_last_z",     "LastCapsuleZ")

print("\n=== Exec 연결 ===")
connect("entry",          "then",         "set_offset",     "execute")
connect("set_offset",     "then",         "set_rel",        "execute")
connect("set_rel",        "then",         "set_last_z",     "execute")

print("\n=== 기본값 설정 ===")
set_default("clamp",    "Min",         "-30.0")
set_default("clamp",    "Max",         "30.0")
set_default("finterp",  "Target",      "0.0")
set_default("finterp",  "InterpSpeed", "18.0")
set_default("make_vec", "X",           "0.0")
set_default("make_vec", "Y",           "0.0")

print("\n=== 완료 ===")
