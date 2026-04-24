"""
GroundMoving.uasset 에서 Sprint_to_Battle_Jog 4종 FName index 찾고,
각 AnimSequence 레퍼런스가 binary 어디에 등장하는지 offset 나열.
인근 바이트 패턴으로 어느 sub-chooser 섹션에 포함되는지 추정.
"""
import os, struct, re, sys

PATH = r"E:\Perforce\SB2\Workspace\Internal\SB2\Content\Art\Character\PC\PC_01\StateMachine\GroundMoving.uasset"

with open(PATH, "rb") as f:
    data = f.read()

print(f"file size: {len(data)} bytes")

# --- find FName entries (length-prefixed strings) by scanning for null-terminated ASCII
# UE FNameEntrySerialized 는 대개 int32 length + ascii|utf16 + terminator. 여기선 쉽게 substring 으로 검색.
targets_str = [
    b"P_Player_Transition_Sprint_to_Battle_Jog_F_Lfoot\x00",
    b"P_Player_Transition_Sprint_to_Battle_Jog_B_Lfoot\x00",
    b"P_Player_Transition_Sprint_to_Battle_Jog_LL_Lfoot\x00",
    b"P_Player_Transition_Sprint_to_Battle_Jog_RL_Lfoot\x00",
]
sub_chooser_names = [
    b"N_LockOn_Transit_Sprinting\x00",
    b"N_LockOn_Transit_Running\x00",
    b"N_LockOn_Transit_Jogging\x00",
    b"N_LockOn_Transit_Walking\x00",
    b"N_LockOn_TransitToGroundMoving\x00",
    b"N_LockOn_GroundMoving\x00",
    b"N_TransitToGroundMoving_Peaceful\x00",
    b"N_TransitToGroundMoving_Battle\x00",
    b"N_GroundMoving_Peaceful\x00",
    b"N_GroundMoving_Battle\x00",
    b"N_GroundMoving_Guarding\x00",
    b"N_TransitToGroundMoving_Guarding\x00",
    b"N_AfterEvade\x00",
    b"N_LockOn_AfterEvade\x00",
    b"N_Moving_Land_Peaceful\x00",
    b"M_Moving_Land_Battle\x00",
    b"N_Wriggle_GroundMoving\x00",
    b"N_Wriggle_TransitToGroundMoving\x00",
]
col_names = [
    b"IsLockOn\x00",
    b"StateMachineMoveState\x00",
    b"AnimStance\x00",
    b"PrevMovementMode\x00",
    b"OverlayPoseState\x00",
    b"HasEvade\x00",
    b"TrjIsCircling\x00",
    b"InWriggle\x00",
    b"WriggleEnd\x00",
]

def find_all(needle):
    positions = []
    start = 0
    while True:
        idx = data.find(needle, start)
        if idx == -1:
            break
        positions.append(idx)
        start = idx + 1
    return positions

print("\n=== FName string positions in name table (offset, name) ===")
name_offsets = {}
for n in targets_str + sub_chooser_names + col_names:
    pos = find_all(n)
    if pos:
        # name table entry 는 이전 int32 length byte 를 포함
        name_offsets[n.rstrip(b"\x00").decode("ascii")] = pos
        print(f"  {n.rstrip(chr(0).encode()).decode():40s} offsets: {pos}")

# --- Sprint_to_Battle_Jog 패키지 경로 오프셋
print("\n=== Sprint_to_Battle_Jog PACKAGE PATHS offsets ===")
for n in [
    b"/Game/Art/Character/PC/PC_01/Animation/Body/Jog/P_Player_Transition_Sprint_to_Battle_Jog_F_Lfoot\x00",
    b"/Game/Art/Character/PC/PC_01/Animation/Body/Jog/P_Player_Transition_Sprint_to_Battle_Jog_B_Lfoot\x00",
    b"/Game/Art/Character/PC/PC_01/Animation/Body/Jog/P_Player_Transition_Sprint_to_Battle_Jog_LL_Lfoot\x00",
    b"/Game/Art/Character/PC/PC_01/Animation/Body/Jog/P_Player_Transition_Sprint_to_Battle_Jog_RL_Lfoot\x00",
]:
    pos = find_all(n)
    print(f"  {n[-55:].rstrip(chr(0).encode()).decode():55s} -> offsets: {pos}")

# --- offset 사이 순서로, 각 sub-chooser 이름 시작 offset 과 비교해서 어느 구간에 Sprint_to_Battle_Jog 가 들어가는지
print("\n=== Offsets map (sub-chooser name offsets) ===")
sc_map = []
for n in sub_chooser_names:
    key = n.rstrip(b"\x00").decode()
    if key in name_offsets:
        for off in name_offsets[key]:
            sc_map.append((off, key))
sc_map.sort()
for off, key in sc_map:
    print(f"  offset {off:>7}  {key}")
