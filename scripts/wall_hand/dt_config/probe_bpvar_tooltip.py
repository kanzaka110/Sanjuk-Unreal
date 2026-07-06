# -*- coding: utf-8 -*-
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/probe_bpvar_tooltip.txt"
res = []
try:
    fns = [a for a in dir(unreal.BlueprintEditorLibrary) if not a.startswith("_")]
    res.append("BlueprintEditorLibrary fns:")
    res.append(", ".join(fns))
    hits = [f for f in fns if "variable" in f or "meta" in f or "tooltip" in f]
    res.append("HITS: " + ", ".join(hits))
except Exception:
    res.append("FATAL\n" + traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(res))
