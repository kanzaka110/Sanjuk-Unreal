import re
from collections import Counter

PC_FILE = r"C:/Dev/Sanjuk-Unreal/scripts/output/pc01_step_only_sync_missing_2026-05-19.txt"

with open(PC_FILE, "r", encoding="utf-8") as f:
    paths = [l.strip() for l in f if l.strip()]

folders = []
for p in paths:
    p2 = p.replace("\\", "/")
    m = re.search(r"/PC_01/Animation/([^/]+)/([^/]+)", p2)
    if m:
        folders.append(f"{m.group(1)}/{m.group(2)}")
    else:
        folders.append("OTHER")

print(f"=== PC_01 미적용 총: {len(paths)} ===\n")

# locomotion 추정 폴더
LOCOMOTION = {"Body/Run", "Body/Walk", "Body/Sprint", "Body/Jog", "Body/Strafe",
              "Body/WriggleMove", "Body/Crouch", "Body/Slope", "Body/Slide",
              "Body/Traversal", "Body/Idle"}

print("=== Animation 2단계 폴더별 ===")
for folder, cnt in sorted(Counter(folders).items(), key=lambda x: -x[1]):
    tag = "  ← LOCOMOTION" if folder in LOCOMOTION else ""
    print(f"{cnt:4d}  {folder}{tag}")

print("\n=== OTHER 53개 상세 (Body/하위 폴더, 또는 Animation/Body 외) ===")
other_folders = []
for p in paths:
    p2 = p.replace("\\", "/")
    m = re.search(r"/PC_01/Animation/(.+?)/[^/]+\.uasset$", p2)
    if m:
        parts = m.group(1).split("/")
        # group 2단계 OTHER인 것은 Animation/Body 외 또는 더 깊은 구조
        full = "/".join(parts[:3]) if len(parts) >= 3 else "/".join(parts)
        other_folders.append(full)

# OTHER로 잡혔던 것만 추출
other_seen = []
for p in paths:
    p2 = p.replace("\\", "/")
    m = re.search(r"/PC_01/Animation/([^/]+)/([^/]+)", p2)
    if not m:
        # 직접 보기
        m2 = re.search(r"/PC_01/Animation/(.+)$", p2)
        if m2:
            other_seen.append(m2.group(1)[:80])

# Animation/Body 외 분포
non_body = []
for p in paths:
    p2 = p.replace("\\", "/")
    m = re.search(r"/PC_01/Animation/([^/]+)", p2)
    if m and m.group(1) != "Body":
        m2 = re.search(r"/PC_01/Animation/([^/]+)/([^/]+)?", p2)
        if m2:
            non_body.append(f"{m2.group(1)}/{m2.group(2) or ''}")

for folder, cnt in sorted(Counter(non_body).items(), key=lambda x: -x[1]):
    print(f"{cnt:4d}  {folder}")
