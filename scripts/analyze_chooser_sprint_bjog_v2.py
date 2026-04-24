"""
v2: Sprint_to_Battle_Jog 의 두 번째 등장 (29777~29949) 주변 데이터 구간에 어떤
sub-chooser 이름 또는 AnimSequence 레퍼런스가 배치되어 있는지 살펴
어느 sub-chooser 섹션에 속하는지 판단.
"""
import re

PATH = r"E:\Perforce\SB2\Workspace\Internal\SB2\Content\Art\Character\PC\PC_01\StateMachine\GroundMoving.uasset"

with open(PATH, "rb") as f:
    data = f.read()

# Sprint_to_Battle_Jog 4종 두 번째 등장
s2_starts = {
    "F":  29834,
    "B":  29777,
    "LL": 29891,
    "RL": 29949,
}
print("=== Second-appearance offsets (expect chooser cell region) ===")
for k, off in sorted(s2_starts.items(), key=lambda x: x[1]):
    print(f"  {k}: {off}")

# +- 2000 바이트 dump 하여 printable string 추출
LOW = 28000
HIGH = 32000
region = data[LOW:HIGH]
print(f"\n=== Region [{LOW}:{HIGH}] printable strings (len>=4) ===")
cur = []
cur_off = LOW
for i, b in enumerate(region):
    if 32 <= b < 127:
        cur.append(chr(b))
    else:
        if len(cur) >= 4:
            s = "".join(cur)
            # 관심있는 놈만 필터링
            if any(x in s for x in [
                "N_LockOn", "N_Ground", "N_Transit", "N_After", "N_Wriggle",
                "M_Moving", "N_Moving",
                "Sprint_to_Battle_Jog", "Walk_to_Jog", "Jog_to_Run", "Walk_to_Sprint",
                "Transition", "Start_F", "Walk_Start", "Jog_Start", "Run_to_",
                "IsLockOn", "StateMachineMoveState", "AnimStance", "PrevMovementMode",
                "TrjIsCircling", "OverlayPoseState",
                "ChooserColumn", "OutputPropertyBinding", "Column",
                "None", "Booleo", "Sprint", "Running", "Jogging",
                "Walking"
            ]):
                print(f"  @{LOW+i-len(cur):>7}: {s}")
        cur = []
print()

# 특정 패턴: Sprint_to_Battle_Jog F 28 bytes 주변 hex
print("=== hex dump 주변 Sprint_to_Battle_Jog_F (@29834) ===")
start = 29834 - 32
for i in range(0, 128, 16):
    addr = start + i
    chunk = data[addr:addr+16]
    hexs = " ".join(f"{b:02x}" for b in chunk)
    asc = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
    print(f"  {addr:>7} | {hexs:<48} | {asc}")
