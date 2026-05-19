import re
from collections import Counter

PC_FILE = r"C:/Dev/Sanjuk-Unreal/scripts/output/pc01_step_only_sync_missing_2026-05-19.txt"
CLEAN_FILE = r"C:/Dev/Sanjuk-Unreal/scripts/output/pc01_animseq_step_only_sync_missing_2026-05-19.txt"

with open(PC_FILE, "r", encoding="utf-8") as f:
    paths = [l.strip() for l in f if l.strip()]

clean = []
for p in paths:
    p2 = p.replace("\\", "/")
    if "/PC_01/Animation/Body/" in p2:
        clean.append(p2)

clean.sort()

with open(CLEAN_FILE, "w", encoding="utf-8") as f:
    for p in clean:
        f.write(p + "\n")

print(f"=== 정제: PC_01/Animation/Body/ 하위만 = {len(clean)} 개 ===\n")

# 폴더별 분포
folders = []
for p in clean:
    m = re.search(r"/Animation/Body/([^/]+)", p)
    if m:
        folders.append(m.group(1))

print("=== Body 1단계 분포 ===")
for k, c in sorted(Counter(folders).items(), key=lambda x: -x[1]):
    print(f"{c:4d}  Body/{k}")

# Locomotion 후보 폴더 더 깊이
print("\n=== Run/Walk/Sprint/Jog 안에서 미적용된 시퀀스 (locomotion 핵심) ===")
loco_kw = ("Run", "Walk", "Sprint", "Jog", "Strafe", "Slide", "Slope")
for p in clean:
    m = re.search(r"/Animation/Body/([^/]+)", p)
    if m and any(kw in m.group(1) for kw in loco_kw):
        name = p.rsplit("/", 1)[-1].replace(".uasset", "")
        print(f"  {name}  [{m.group(1)}]")
