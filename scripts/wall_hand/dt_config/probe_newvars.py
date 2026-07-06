# -*- coding: utf-8 -*-
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/probe_newvars.txt"
res = []
try:
    bp = unreal.EditorAssetLibrary.load_asset("/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP")
    try:
        nv = bp.get_editor_property("NewVariables")
        res.append(f"NewVariables OK n={len(nv)}")
        v0 = nv[0]
        res.append(f"v0 type={type(v0).__name__}")
        res.append("v0 props: " + ", ".join(a for a in dir(v0) if not a.startswith("_"))[:300])
        try:
            md = v0.get_editor_property("MetaDataArray")
            res.append(f"MetaDataArray OK n={len(md)} sample={md[0] if len(md) else None}")
        except Exception as e:
            res.append(f"MetaDataArray FAIL {e}")
    except Exception as e:
        res.append(f"NewVariables FAIL {e}")
except Exception:
    res.append("FATAL\n" + traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(res))
