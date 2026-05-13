"""Phase 3: locate PropertyAccess_1, inspect VariableGet_12/13 properly, check ABP vars list for missing names."""
import json

def load_inner(path):
    with open(path,'r',encoding='utf-8') as f:
        d=json.load(f)
    return json.loads(d['result']['content'][0]['text'])

def load_simple(path):
    with open(path,'r',encoding='utf-8') as f:
        return json.load(f)

dd = load_inner('Saved/drawdebug_bp.json')

# Inspect both PropertyAccess nodes deeply (dump every field)
for n in dd['nodes']:
    if n['class']=='K2Node_PropertyAccess':
        print(f"\n=== {n['id']} ===")
        print(json.dumps(n, indent=2, ensure_ascii=False))

# Find variables: read abp_all_vars_pre.json
print('\n\n=== ABP var names (from abp_all_vars_pre.json) ===')
vars_raw = load_simple('Saved/abp_all_vars_pre.json')
# Try multiple shapes
def extract_vars(obj):
    out=[]
    if isinstance(obj, dict):
        if 'variables' in obj:
            for v in obj['variables']:
                if isinstance(v, dict):
                    out.append(v.get('name') or v.get('Name') or str(v))
                else:
                    out.append(str(v))
            return out
        if 'result' in obj:
            r = obj['result']
            if isinstance(r,dict) and 'content' in r:
                txt = r['content'][0].get('text','{}') if r['content'] else '{}'
                try:
                    inner = json.loads(txt)
                    return extract_vars(inner)
                except Exception as e:
                    print('parse err', e)
            return extract_vars(r)
    if isinstance(obj, list):
        for it in obj:
            n = it.get('name') if isinstance(it,dict) else str(it)
            if n: out.append(n)
    return out

names = extract_vars(vars_raw)
print(f"  total: {len(names)}")

# Search for specific suspicions
suspects = [
    'PrevWalkMode','OffsetRootMode','TrjPastAngularVelocity_Z','TrjCurrentAngularVelocity_Z',
    'MatchedConfigIndex','HeightDiff','DiffOnGround','UpperBodyBlendWeight',
    'TrjPastAngularVelocity','TrjCurrentAngularVelocity','OverlayPoseState','OverlayWeight',
    'CurrentFootIKWeight','TrjFutureVelocity','Acceleration','MovementMode','MoveSide',
    'PendingWalkMode','AnimStance','AnimTag','IsBattle','IsStrafe','JustExitedSprint',
    'ResetOffsetPulse','IsSequenceBindingActor','IsBlocked','IsLockOn','TrjIsCircling','HasEvade',
    'TargetRotationDelta','TrjTurnAngle','CircleStrafeHysteresis','HoldTimeThreshold',
    'IsFullBodySlotActive','FullBodySlotWeight','WriggleEnd','InWriggle','MovementState',
    'CurrentMovementMode'
]
for s in suspects:
    matches = [n for n in names if s.lower() in (n or '').lower()]
    print(f"  {s:35s}: {matches}")
