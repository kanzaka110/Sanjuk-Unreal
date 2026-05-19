import re
from collections import Counter

PC_FILE = r"C:/Dev/Sanjuk-Unreal/scripts/output/pc01_step_only_sync_missing_2026-05-19.txt"

with open(PC_FILE, "r", encoding="utf-8") as f:
    paths = [l.strip() for l in f if l.strip()]

# 첫 정규식 안 맞은 것들 (OTHER)을 그대로 보기
others = []
for p in paths:
    p2 = p.replace("\\", "/")
    m = re.search(r"/PC_01/Animation/([^/]+)/([^/]+)", p2)
    if not m:
        # /PC_01/Animation/ 뒤를 보여줌
        m2 = re.search(r"/PC_01/Animation/(.+)$", p2)
        if m2:
            others.append(m2.group(1))
        else:
            others.append(p2)

print(f"=== OTHER 총: {len(others)} ===\n")
print("=== 샘플 30개 ===")
for o in others[:30]:
    print(f"  {o}")

# 폴더 깊이별 패턴
patterns = []
for o in others:
    parts = o.split("/")
    if len(parts) == 1:
        patterns.append("ROOT")
    else:
        patterns.append(parts[0])

print(f"\n=== 폴더 패턴 ===")
for k, c in sorted(Counter(patterns).items(), key=lambda x: -x[1]):
    print(f"{c:4d}  {k}")
