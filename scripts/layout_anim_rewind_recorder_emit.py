"""
ABRR Layout Cleanup
====================
Reorganizes the AnimRewindRecorderEmit function graph in /Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP
into 10 vertical column categories with comment boxes per category.

- Wires are NOT touched (only positions move).
- New nodes are ONLY comment boxes.
- Uses Monolith HTTP API batch_execute for efficiency.

Author: AnimBP Tuner (2026-05-15)
"""
import json
import urllib.request

ASSET = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GRAPH = "AnimRewindRecorderEmit"
URL = "http://localhost:9316/mcp"


def rpc(method, params, request_id=1, timeout=120):
    body = json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}).encode("utf-8")
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def tool_call(action, params, request_id=1, tool="blueprint_query"):
    return rpc("tools/call",
               {"name": tool, "arguments": {"action": action, "params": params}},
               request_id=request_id)


def parse_text_payload(resp):
    """Monolith wraps results in result.content[0].text as JSON-encoded string."""
    try:
        return json.loads(resp["result"]["content"][0]["text"])
    except Exception:
        return resp


# -----------------------------------------------------------------------------
# LAYOUT PLAN
# -----------------------------------------------------------------------------
# Coordinate system:
#   x = 0          : FunctionEntry
#   x = 250        : VG_0 bAnimRewindRecording (gate)
#   x = 550        : Branch (IfThenElse_0)
#   x = 850        : VariableSet (Set RewindMonitorLine)
#   x = 1200       : PrintText (CallFunction_1) below VariableSet
#   x = 1600..7800 : 10 category columns (600px wide each)
#   x = 8400       : FormatText_1
# Each category column has a comment box header.

COL_WIDTH = 700        # spacing between category columns
COL_HEADER_Y = 100     # comment box header y
COL_NODES_Y_START = 280  # first node in column
STEP_VG = 110          # vertical step between VariableGet nodes
STEP_CF = 140          # vertical step between CallFunction nodes

# Each category: (name, start_x, color {r,g,b,a}, [node_id, ...] ordered top to bottom)
# Node ordering inside a column follows logical grouping (helpers near consumers).
CATEGORIES = [
    {
        "name": "1. Frame_Basics",
        "x": 1600,
        "color": {"r": 1.0, "g": 0.95, "b": 0.30, "a": 0.55},  # yellow
        "nodes": [
            "K2Node_CallFunction_0",   # Get Frame Count  -> FT.f
            "K2Node_VariableGet_1",    # Speed2D -> FT.sp
            "K2Node_VariableGet_4",    # bIsStart -> FT.ist
            "K2Node_VariableGet_5",    # HasEvade -> FT.he
            "K2Node_VariableGet_6",    # Velocity (helper for CF_4)
            "K2Node_CallFunction_4",   # Vector Length XY -> FT.vlen
            "K2Node_VariableGet_2",    # AnimStance (helper for CF_2)
            "K2Node_CallFunction_2",   # To String (Byte) -> FT.as
            "K2Node_VariableGet_3",    # MovementState (helper for CF_3)
            "K2Node_CallFunction_3",   # To String (Byte) -> FT.ms
            "K2Node_VariableGet_7",    # PendingWalkMode (helper for CF_5)
            "K2Node_CallFunction_5",   # To String (Byte) -> FT.pwm
            "K2Node_VariableGet_8",    # IsLockOn -> FT.il
            "K2Node_VariableGet_9",    # IsStrafe -> FT.isf
            "K2Node_VariableGet_10",   # TrjIsCircling -> FT.isc
            "K2Node_VariableGet_11",   # CircleStrafeHysteresis -> FT.csh
            "K2Node_VariableGet_12",   # TargetRotationDelta -> FT.trd
            "K2Node_VariableGet_13",   # IsBattle -> FT.ib
            "K2Node_VariableGet_14",   # RuleMoveFlag -> FT.rmf
        ],
    },
    {
        "name": "2. IK_Foot",
        "x": 2300,
        "color": {"r": 1.0, "g": 0.55, "b": 0.10, "a": 0.55},  # orange
        "nodes": [
            "K2Node_VariableGet_15",   # FootIKWeight -> FT.fik
            "K2Node_VariableGet_16",   # FootClampAlpha -> FT.fca
            "K2Node_VariableGet_17",   # OverlayWeight -> FT.ow
            "K2Node_VariableGet_18",   # IsGuarding -> FT.ig
            "K2Node_VariableGet_19",   # SearchCost -> FT.sc
        ],
    },
    {
        "name": "3. Animation",
        "x": 3000,
        "color": {"r": 0.65, "g": 0.30, "b": 0.85, "a": 0.55},  # purple
        "nodes": [
            "K2Node_VariableGet_20",   # CurrAnimTag -> FT.clip
            "K2Node_VariableGet_25",   # CurrentSequenceName -> FT.seq
            "K2Node_VariableGet_21",   # bIsMoving -> FT.bim
            "K2Node_VariableGet_22",   # bPrevIsMoving -> FT.bpim
            "K2Node_VariableGet_23",   # MoveSide (helper)
            "K2Node_CallFunction_6",   # To String -> FT.ms_l
            "K2Node_VariableGet_24",   # PrevMoveSide (helper)
            "K2Node_CallFunction_7",   # To String -> FT.ms_p
        ],
    },
    {
        "name": "4. MotionMatching",
        "x": 3700,
        "color": {"r": 0.20, "g": 0.55, "b": 1.00, "a": 0.55},  # blue
        "nodes": [
            "K2Node_CallFunction_34",  # Get Enumerator Name -> FT.mm
            "K2Node_CallFunction_32",  # Get Enumerator Name -> FT.ops
            "K2Node_VariableGet_33",   # FullBodySlotWeight -> FT.fbsw
            "K2Node_VariableGet_34",   # IsFullBodySlotActive -> FT.fa
            "K2Node_VariableGet_39",   # ResetOffsetPulse -> FT.rop
            "K2Node_VariableGet_31",   # IsSequenceBindingActor -> FT.sba
            "K2Node_VariableGet_30",   # IsBlocked -> FT.ibk
            "K2Node_VariableGet_37",   # WriggleEnd -> FT.we
            "K2Node_VariableGet_36",   # InWriggle -> FT.iw
            "K2Node_VariableGet_27",   # JustExitedSprint -> FT.jes
        ],
    },
    {
        "name": "5. Thresholds",
        "x": 4400,
        "color": {"r": 0.20, "g": 0.85, "b": 0.85, "a": 0.55},  # teal
        "nodes": [
            "K2Node_VariableGet_38",   # HoldTimeThreshold -> FT.htt
            "K2Node_CallFunction_8",   # Should Turn in Place -> FT.stip
            "K2Node_CallFunction_16",  # Is Pivoting -> FT.ip
            "K2Node_CallFunction_18",  # Get Lean Amount -> FT.lm
            "K2Node_CallFunction_39",  # Get Curve Value (Disable_AdditiveLean) -> FT.dal
            "K2Node_VariableGet_43",   # bIsSprintEndTransition -> FT.sset
        ],
    },
    {
        "name": "6. Phase_Eval",
        "x": 5100,
        "color": {"r": 1.00, "g": 0.50, "b": 0.65, "a": 0.55},  # pink
        "nodes": [
            "K2Node_CallFunction_37",  # GetCurveValue (Phase) -> FT.phase
            "K2Node_CallFunction_38",  # GetCurveValue (enable_orientationwarping) -> FT.eow
            "K2Node_CallFunction_36",  # GetCurveValue (enable_playratewarping) -> FT.eprw
            "K2Node_VariableGet_40",   # TrjFutureVelocity (helper)
            "K2Node_CallFunction_19",  # Vector Length XY -> FT.fv
            "K2Node_VariableGet_41",   # Acceleration (helper)
            "K2Node_CallFunction_20",  # Vector Length XY -> FT.acc
            "K2Node_CallFunction_11",  # IsSlotActive (FullBody) -> FT.isafb
            "K2Node_CallFunction_9",   # IsSlotActive (UpperBody) -> FT.isaub
            "K2Node_CallFunction_13",  # GetSlotLocalWeight -> FT.sswseq
        ],
    },
    {
        "name": "7. Weight_Curve",
        "x": 5800,
        "color": {"r": 0.65, "g": 0.45, "b": 0.25, "a": 0.55},  # brown
        "nodes": [
            "K2Node_CallFunction_33",  # GetEnumeratorName -> FT.rva
            "K2Node_CallFunction_35",  # GetEnumeratorName -> FT.wt
            "K2Node_VariableGet_35",   # UpperBodyBlendWeight -> FT.ubsw
            "K2Node_VariableGet_42",   # SBCharacterMovement (helper for CF_30 & CF_12)
            "K2Node_CallFunction_30",  # CanVaultCurrentObstacle -> FT.cvco
        ],
    },
    {
        "name": "8. Travel",
        "x": 6500,
        "color": {"r": 0.55, "g": 0.55, "b": 0.55, "a": 0.55},  # grey
        "nodes": [
            "K2Node_CallFunction_12",  # GetCurrentTravelActionResult (output unwired but node present)
            "K2Node_CallFunction_17",  # GetWriggleMoveType (orphan helper)
        ],
    },
    {
        "name": "9. Trajectory",
        "x": 7200,
        "color": {"r": 0.55, "g": 0.55, "b": 0.55, "a": 0.55},  # grey
        "nodes": [
            "K2Node_VariableGet_28",   # TrjPastAngularVelocity (orphan)
            "K2Node_VariableGet_29",   # TrjCurrentAngularVelocity (orphan)
            "K2Node_VariableGet_26",   # MovementMode (orphan)
            "K2Node_VariableGet_32",   # OverlayPoseState (orphan)
        ],
    },
    {
        "name": "10. StateMachine",
        "x": 7900,
        "color": {"r": 0.30, "g": 0.80, "b": 0.40, "a": 0.55},  # green
        "nodes": [
            "K2Node_VariableGet_44",   # StateMachineMoveState (helper)
            "K2Node_CallFunction_31",  # To String (Byte) -> FT.sms
            "K2Node_VariableGet_45",   # NullAnim -> FT.na
            "K2Node_VariableGet_46",   # RunRetransit -> FT.rrt
            "K2Node_VariableGet_47",   # RetransitReason -> FT.rrr
        ],
    },
]

# Backbone (left-side execution chain)
BACKBONE = [
    ("K2Node_FunctionEntry_0", 0, 0),
    ("K2Node_VariableGet_0",   220, 180),     # bAnimRewindRecording (condition)
    ("K2Node_IfThenElse_0",    520, 0),       # Branch
    ("K2Node_VariableSet_0",   820, 0),       # Set RewindMonitorLine
    ("K2Node_CallFunction_1", 1180, 280),     # Print Text (chained after VariableSet)
]

# FormatText: place far right
FT_POS = (8700, 0)

# -----------------------------------------------------------------------------
# Build batch operations
# -----------------------------------------------------------------------------
def build_position_ops():
    """Return a list of {op:'set_node_position', node_id, position} for all 80 nodes."""
    ops = []
    # Backbone
    for nid, x, y in BACKBONE:
        ops.append({"op": "set_node_position", "node_id": nid, "position": [x, y], "graph_name": GRAPH})

    # FormatText
    ops.append({"op": "set_node_position", "node_id": "K2Node_FormatText_1",
                "position": list(FT_POS), "graph_name": GRAPH})

    # Categories
    for cat in CATEGORIES:
        x = cat["x"]
        y = COL_NODES_Y_START
        for nid in cat["nodes"]:
            ops.append({"op": "set_node_position", "node_id": nid,
                        "position": [x, y], "graph_name": GRAPH})
            # decide step by node class via prefix
            if nid.startswith("K2Node_CallFunction") or nid.startswith("K2Node_GetEnumeratorNameAsString"):
                y += STEP_CF
            else:
                y += STEP_VG
    return ops


def all_used_nodes():
    used = {nid for nid, _, _ in BACKBONE}
    used.add("K2Node_FormatText_1")
    for cat in CATEGORIES:
        used.update(cat["nodes"])
    return used


def print_summary(ops):
    print(f"[summary] backbone+ft = {len(BACKBONE)+1}")
    by_cat = {c['name']: len(c['nodes']) for c in CATEGORIES}
    for k, v in by_cat.items():
        print(f"  {k}: {v}")
    print(f"  TOTAL set_node_position ops: {len(ops)}")


def step1_backup_dump():
    """Get current graph state (pre-layout)."""
    resp = tool_call("get_graph_data",
                     {"asset_path": ASSET, "graph_name": GRAPH},
                     request_id=10)
    out = parse_text_payload(resp)
    with open(r"C:\Dev\Sanjuk-Unreal\Saved\PROBE_AnimRewindRecorderEmit_pre_layout_20260515.json",
              "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    nodes = out.get("nodes", []) if isinstance(out, dict) else []
    print(f"[step1] pre-layout dump: {len(nodes)} nodes")
    return nodes


def step2_apply_layout(ops, dry_run=False):
    if dry_run:
        print("[step2-DRY] would call batch_execute with", len(ops), "operations")
        return None
    resp = tool_call("batch_execute",
                     {"asset_path": ASSET,
                      "operations": ops,
                      "compile_on_complete": False,
                      "stop_on_error": False},
                     request_id=20)
    out = parse_text_payload(resp)
    return out


def step3_add_comments():
    """Add one comment box per category, enclosing its nodes (auto-size)."""
    results = []
    for i, cat in enumerate(CATEGORIES):
        params = {
            "asset_path": ASSET,
            "graph_name": GRAPH,
            "text": cat["name"],
            "node_ids": cat["nodes"],
            "color": cat["color"],
            "font_size": 22,
        }
        resp = tool_call("add_comment_node", params, request_id=30 + i)
        out = parse_text_payload(resp)
        results.append({"category": cat["name"], "result": out})
    return results


def step4_compile():
    resp = tool_call("compile_blueprint", {"asset_path": ASSET}, request_id=40)
    return parse_text_payload(resp)


def step5_save():
    resp = tool_call("save_asset", {"asset_path": ASSET}, request_id=50)
    return parse_text_payload(resp)


def step6_postdump():
    resp = tool_call("get_graph_data",
                     {"asset_path": ASSET, "graph_name": GRAPH},
                     request_id=60)
    out = parse_text_payload(resp)
    with open(r"C:\Dev\Sanjuk-Unreal\Saved\PROBE_AnimRewindRecorderEmit_clean_layout_20260515.json",
              "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    return out


def main():
    print("=" * 70)
    print("ABRR Layout Cleanup — 2026-05-15")
    print("=" * 70)

    # Step 1: Pre-layout dump
    pre_nodes = step1_backup_dump()
    pre_ids = {n["id"] for n in pre_nodes}

    # Sanity check: every node we plan to move must exist
    planned = all_used_nodes()
    missing = planned - pre_ids
    extra = pre_ids - planned
    if missing:
        print("[ABORT] Planned-but-missing nodes:", missing)
        return
    if extra:
        print("[WARN] Live-but-unplanned nodes (will not be moved):", extra)

    ops = build_position_ops()
    print_summary(ops)

    # Step 2: Apply positions
    print("\n[step2] Applying batch set_node_position ...")
    r2 = step2_apply_layout(ops)
    if r2 is None:
        print("  (dry-run skipped)")
    else:
        with open(r"C:\Dev\Sanjuk-Unreal\Saved\ABRR_layout_batch_result.json",
                  "w", encoding="utf-8") as f:
            json.dump(r2, f, indent=2, ensure_ascii=False)
        succ = r2.get("succeeded", r2.get("success_count", "?"))
        fail = r2.get("failed", r2.get("failure_count", "?"))
        print(f"  batch result: succeeded={succ} failed={fail}")
        if isinstance(r2, dict) and r2.get("results"):
            errors = [x for x in r2["results"] if not x.get("success", True)]
            if errors:
                print(f"  errors ({len(errors)}):")
                for e in errors[:5]:
                    print("   ", e)

    # Step 3: Comment boxes
    print("\n[step3] Adding category comment boxes ...")
    cmts = step3_add_comments()
    with open(r"C:\Dev\Sanjuk-Unreal\Saved\ABRR_layout_comments_result.json",
              "w", encoding="utf-8") as f:
        json.dump(cmts, f, indent=2, ensure_ascii=False)
    ok = 0
    for c in cmts:
        r = c["result"]
        if isinstance(r, dict) and not r.get("error"):
            ok += 1
            print(f"  + {c['category']}: OK")
        else:
            print(f"  ! {c['category']}: {r}")
    print(f"  comment boxes added: {ok}/{len(cmts)}")

    # Step 4: Compile
    print("\n[step4] Compile ...")
    rcmp = step4_compile()
    print(" ", json.dumps(rcmp, ensure_ascii=False)[:300])

    # Step 5: Save
    print("\n[step5] Save ...")
    rsav = step5_save()
    print(" ", json.dumps(rsav, ensure_ascii=False)[:300])

    # Step 6: Post-layout dump
    print("\n[step6] Post-layout dump ...")
    post = step6_postdump()
    post_nodes = post.get("nodes", []) if isinstance(post, dict) else []
    print(f"  post-layout: {len(post_nodes)} nodes")


if __name__ == "__main__":
    main()
