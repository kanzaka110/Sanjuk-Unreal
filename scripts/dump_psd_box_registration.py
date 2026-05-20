"""모든 PC_01 PSD 에 Box / Pivot / Stop 클립 등록 여부 dump.

새 가설 검증: Box 클립이 어느 PSD 에도 등록되어 있지 않아서
Pose Search 가 빈 결과를 반환하고 continuing pose 유지로 매칭 실패.

실행:
  UE Editor > Output Log > py "C:/Dev/Sanjuk-Unreal/scripts/dump_psd_box_registration.py"
"""
import unreal

PSD_ROOT = "/Game/Art/Character/PC/PC_01/MotionMatching/PSD"
PATTERNS = ["_Box_", "_Pivot_", "_Stop_", "_Start_"]


def list_psd_assets():
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    results = reg.get_assets_by_path(PSD_ROOT, recursive=True)
    out = []
    for ad in results:
        cls = ad.get_class().get_name() if ad.get_class() else "?"
        if cls == "PoseSearchDatabase":
            out.append(str(ad.package_name))
    return sorted(out)


def get_psd_anim_list(psd_path: str):
    psd = unreal.load_asset(psd_path)
    if psd is None:
        return None
    try:
        anim_objs = psd.get_editor_property("AnimationAssets")
    except Exception as e:
        return f"AnimationAssets error: {e}"
    seqs = []
    for entry in anim_objs:
        # entry is FInstancedStruct. extract Sequence reference via export_text
        try:
            exp = entry.export_text() if hasattr(entry, "export_text") else repr(entry)
            seqs.append(exp)
        except Exception as e:
            seqs.append(f"<export err: {e}>")
    return seqs


def categorize(seq_export: str):
    matched = []
    for p in PATTERNS:
        if p in seq_export:
            matched.append(p)
    return matched


def dump_psd(psd_path: str):
    short = psd_path.split("/")[-1]
    print(f"\n--- {short} ({psd_path}) ---")
    entries = get_psd_anim_list(psd_path)
    if entries is None:
        print("  load failed")
        return
    if isinstance(entries, str):
        print(f"  {entries}")
        return

    # 카운터
    counters = {p: 0 for p in PATTERNS}
    others = 0
    samples = {p: [] for p in PATTERNS}

    for exp in entries:
        pats = categorize(exp)
        if not pats:
            others += 1
        else:
            for p in pats:
                counters[p] += 1
                if len(samples[p]) < 3:
                    # Extract clip name from export
                    idx = exp.find("P_Player_Fist")
                    if idx >= 0:
                        end = exp.find("'", idx)
                        if end < 0:
                            end = exp.find(",", idx)
                        if end < 0:
                            end = idx + 60
                        samples[p].append(exp[idx:end])
                    else:
                        samples[p].append(exp[:80])

    print(f"  total entries: {len(entries)}")
    for p in PATTERNS:
        print(f"  {p}: count={counters[p]}")
        for s in samples[p]:
            print(f"    e.g. {s}")
    print(f"  (others/loops/transitions etc): {others}")


print(f"========== PC_01 PSD Box/Pivot/Stop/Start registration check ==========")
psd_list = list_psd_assets()
print(f"Found {len(psd_list)} PSD assets:")
for p in psd_list:
    print(f"  - {p}")

for psd_path in psd_list:
    try:
        dump_psd(psd_path)
    except Exception as e:
        print(f"[ERROR] {psd_path}: {e}")

print("\n=== DONE ===")