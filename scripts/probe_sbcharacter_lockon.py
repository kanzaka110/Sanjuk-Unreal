import unreal, json, re

KEYS = re.compile(r"(lockon|sprint|orient|rotation|suppress|disable|force|transition|target|strafe|rootmotion|controlrotation)", re.IGNORECASE)
SKIPVAL = lambda v: isinstance(v, (unreal.Object,)) or (isinstance(v, str) and len(v) > 200)

def dump_class(cls):
    out = {"class": cls.get_name(), "path": cls.get_path_name(), "props": [], "funcs": []}
    try:
        cdo = unreal.get_default_object(cls)
    except Exception:
        cdo = None
    # properties
    try:
        names = list(cls.get_editor_property_names())
    except Exception:
        names = []
    for n in names:
        if not KEYS.search(n):
            continue
        rec = {"name": n}
        if cdo is not None:
            try:
                v = cdo.get_editor_property(n)
                rec["value"] = "<obj>" if SKIPVAL(v) else repr(v)[:160]
            except Exception as e:
                rec["value"] = f"<err:{e}>"
        out["props"].append(rec)
    # functions (via reflection)
    try:
        for fname in dir(cls):
            if fname.startswith("_"):
                continue
            if KEYS.search(fname):
                out["funcs"].append(fname)
    except Exception:
        pass
    return out

def walk_up(cls, max_depth=10):
    chain = []
    cur = cls
    for _ in range(max_depth):
        if cur is None:
            break
        chain.append(cur)
        try:
            cur = cur.get_super_class()
        except Exception:
            break
    return chain

targets = []
for path in ["/Script/SB2.SBCharacter", "/Script/SB2.SBPCActorBase", "/Script/SB2.SBCharacterMovementComponent"]:
    c = unreal.load_class(None, path)
    if c:
        targets.append(c)
        for parent in walk_up(c)[1:]:
            if parent and parent.get_name() not in ("Character", "Pawn", "Actor", "Object", "CharacterMovementComponent", "PawnMovementComponent", "NavMovementComponent", "MovementComponent", "ActorComponent"):
                targets.append(parent)

# also try to find SBCharacter's parent (might not be SBPCActorBase)
sbc = unreal.load_class(None, "/Script/SB2.SBCharacter")
if sbc:
    for p in walk_up(sbc, 6):
        if p and p not in targets:
            targets.append(p)
sbcmc = unreal.load_class(None, "/Script/SB2.SBCharacterMovementComponent")
if sbcmc:
    for p in walk_up(sbcmc, 6):
        if p and p not in targets:
            targets.append(p)

results = []
seen = set()
for t in targets:
    if not t:
        continue
    k = t.get_path_name()
    if k in seen:
        continue
    seen.add(k)
    results.append(dump_class(t))

# Also dump CDO value of LockOnSprintChangeOrientModeTime if found anywhere
focus = {}
for cls_path in ["/Script/SB2.SBCharacter", "/Script/SB2.SBPCActorBase", "/Script/SB2.SBCharacterMovementComponent"]:
    c = unreal.load_class(None, cls_path)
    if not c:
        continue
    try:
        cdo = unreal.get_default_object(c)
        for n in c.get_editor_property_names():
            if "LockOnSprintChangeOrientModeTime" in n or "ChangeOrientMode" in n:
                focus[f"{c.get_name()}.{n}"] = repr(cdo.get_editor_property(n))
    except Exception as e:
        focus[cls_path] = f"err:{e}"

print("=== FOCUS ===")
print(json.dumps(focus, indent=2))
print("=== ALL ===")
print(json.dumps(results, indent=2)[:18000])
