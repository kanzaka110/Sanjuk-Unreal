"""Analyze DrawDebug graph: backtrace each FormatText pin source for ANIM_REC migration."""
import json, sys, re
from collections import defaultdict

def load_inner(path):
    with open(path, 'r', encoding='utf-8') as f:
        d = json.load(f)
    txt = d['result']['content'][0]['text']
    return json.loads(txt)

dd = load_inner('Saved/drawdebug_bp.json')

def index_nodes(g):
    by_id = {n['id']: n for n in g['nodes']}
    pin_index = {}
    for n in g['nodes']:
        for p in n.get('pins', []):
            pin_index[p['id']] = (n['id'], p)
    return by_id, pin_index

dd_nodes, dd_pins = index_nodes(dd)

# Helper: given a node, return pin by name
def get_pin(node, name, direction=None):
    for p in node.get('pins', []):
        if p['name'] == name and (direction is None or p['direction'] == direction):
            return p
    return None

# Helper: trace input pin -> source node/pin
def trace_input(pin):
    """Given a pin dict (input), return list of (src_node_id, src_pin_name) tuples it's connected from.
    pin['connected_to'] contains entries like 'NodeId.pinName' for outputs that feed into this input.
    """
    out = []
    for ref in pin.get('connected_to', []) or []:
        if '.' in ref:
            nid, pname = ref.split('.', 1)
        else:
            nid, pname = ref, None
        out.append((nid, pname))
    return out

def node_summary(nid):
    n = dd_nodes.get(nid)
    if not n:
        return f"<MISSING:{nid}>"
    cls = n['class']
    title = n.get('title','')
    extra = ''
    # Pull useful default values
    for p in n.get('pins', []):
        if p['direction']=='input' and p.get('default_value') is not None and not p.get('connected_to'):
            extra += f" {p['name']}={p['default_value']!r}"
    return f"{nid} [{cls}] title={title!r}{extra}"

# Print every FormatText node with its Format string + input pins
ft_nodes = [n for n in dd['nodes'] if n['class'] == 'K2Node_FormatText']

for ft in ft_nodes:
    print(f"\n=== {ft['id']} ===")
    # Find Format pin (the format string default)
    fmt_pin = get_pin(ft, 'Format', 'input')
    if fmt_pin is None:
        # Some versions show as 'In Format' or default - check all input pins for string with {tokens}
        for p in ft.get('pins', []):
            if p['direction']=='input' and isinstance(p.get('default_value'), str) and '{' in p.get('default_value',''):
                fmt_pin = p
                break
    if fmt_pin:
        fmt_str = fmt_pin.get('default_value', '')
        print(f"  Format: {fmt_str!r}")
    else:
        print('  (no Format pin found)')
        # List all pins for inspection
        for p in ft.get('pins', []):
            print(f"    {p['direction']:6s} {p['name']:30s} type={p.get('type')} default={p.get('default_value')!r} conn={p.get('connected_to')}")
        continue
    # List all input pins (besides Format)
    for p in ft.get('pins', []):
        if p['direction'] != 'input':
            continue
        if p['name'] == fmt_pin['name']:
            continue
        srcs = trace_input(p)
        print(f"  IN  {p['name']:20s} ({p.get('type','?')}) <- ", end='')
        if not srcs:
            print(f"default={p.get('default_value')!r}")
        else:
            for nid, pname in srcs:
                print(f"\n      {node_summary(nid)} :: pin={pname}", end='')
            print()
