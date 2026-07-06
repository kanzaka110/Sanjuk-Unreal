# -*- coding: utf-8 -*-
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/tooltip_subobj.txt"
res = []
try:
    p = "/Game/_WHScratch/S_TooltipTest2.S_TooltipTest2:UserDefinedStructEditorData_0"
    ed = unreal.load_object(None, p)
    res.append(f"subobj={ed}")
    if ed:
        try:
            vd = ed.get_editor_property("VariablesDescriptions")
            res.append(f"VD n={len(vd)} type={type(vd).__name__}")
            e0 = vd[0]
            res.append(f"e0 type={type(e0).__name__}")
            try:
                tt = e0.get_editor_property("ToolTip")
                res.append(f"e0.ToolTip={tt!r}")
                e0.set_editor_property("ToolTip", "PROBE_TT_OK")
                vd[0] = e0
                ed.set_editor_property("VariablesDescriptions", vd)
                vd2 = ed.get_editor_property("VariablesDescriptions")
                res.append(f"after set: {vd2[0].get_editor_property('ToolTip')!r}")
            except Exception as e:
                res.append(f"tooltip member FAIL {e}")
                res.append("e0 dir: " + ", ".join(a for a in dir(e0) if not a.startswith("_"))[:400])
        except Exception as e:
            res.append(f"VD FAIL {e}")
except Exception:
    res.append("FATAL\n" + traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(res))
