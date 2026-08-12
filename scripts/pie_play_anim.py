# -*- coding: utf-8 -*-
"""PIE 플레이어에게 AnimSequence 를 FullBody 슬롯 다이나믹 몽타주로 재생.
사용: play_anim.py <Beta009|LinkAttack01|에셋경로> [playrate] [slomo]
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mono import call

BASE = "/Game/Art/Character/PC/PC_01/Animation/Body/Attack/"
ALIAS = {
    "beta009": BASE + "P_Player_Fist_Normal_Beta009",
    "linkattack01": BASE + "P_Player_Fist_Normal_LinkAttack01_HumanA1",
}

arg = (sys.argv[1] if len(sys.argv) > 1 else "beta009")
asset = ALIAS.get(arg.lower(), arg if arg.startswith("/Game") else BASE + arg)
rate = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
slomo = sys.argv[3] if len(sys.argv) > 3 else None

if slomo:
    print("slomo:", call("editor_query", "run_console_command", command="slomo " + slomo).get("output"))

r = call("editor_query", "pie_call_function", class_name="PC_01", anim_instance=True,
         function="PlaySlotAnimationAsDynamicMontage",
         args={"Asset": asset, "SlotNodeName": "FullBody",
               "BlendInTime": 0.05, "BlendOutTime": 0.15, "InPlayRate": rate,
               "LoopCount": 1, "BlendOutTriggerTime": -1.0, "InTimeToStartMontageAt": 0.0})
print(json.dumps(r, ensure_ascii=False))
