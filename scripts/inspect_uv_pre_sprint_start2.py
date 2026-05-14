import json
d = json.load(open('C:/Dev/Sanjuk-Unreal/Saved/Logs/pre_uv_sprint_start.json'))
txt = d['result']['content'][0]['text']
g = json.loads(txt)
nodes = g.get('nodes', [])
print('total nodes:', len(nodes))
print('keys of g:', list(g.keys()))
print('\n--- First 3 nodes ---')
for n in nodes[:3]:
    print(json.dumps(n, indent=2, ensure_ascii=False)[:500])
    print('---')
