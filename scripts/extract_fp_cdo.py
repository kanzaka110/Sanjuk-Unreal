"""CDO JSON에서 Plant/Interpolation/Pelvis 변수만 뽑아 출력."""
import json

d = json.load(open("cdo.json"))
content = d.get("result", {}).get("content", [])
t = content[0].get("text", "") if content else ""
obj = json.loads(t)
props = obj.get("properties", [])
keywords = ["PlantSettings", "InterpolationSettings", "Pelvis", "FootIK", "FootPlacement"]
wanted = [p for p in props if any(k in p.get("name", "") for k in keywords)]
for p in wanted:
    name = p.get("name")
    ptype = p.get("type")
    print(f"\n=== {name} ({ptype}) ===")
    v = p.get("value", {})
    print(json.dumps(v, indent=2)[:3500])
