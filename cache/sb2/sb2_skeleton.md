# SB2 PC_01 스켈레톤 구조 덤프

수집일: 2026-04-16  
Monolith 버전: 0.12.1  
에셋 경로: `/Game/Art/Character/PC/PC_01/Body/PC_01_Body_001/PC_01_Body_001_Skeleton`

---

## 1. 기본 정보

```
bone_count:     322 (일반 본) + 4 (가상 본) = 326 총합
virtual_bones:  4개
```

---

## 2. 가상 본 (Virtual Bones)

| 이름 | 소스 | 타겟 |
|------|------|------|
| VB ik_root | root | root |
| VB Curves | root | pelvis |
| VB ik_foot_l | VB ik_root | foot_l |
| VB ik_foot_r | VB ik_root | foot_r |

---

## 3. 스켈레톤 계층 구조

### 루트 계층

```
root [0]
├── pelvis [1]
│   ├── spine_01 [2]
│   │   ├── spine_02 [3]
│   │   │   ├── spine_03 [4]
│   │   │   │   ├── spine_04 [5]
│   │   │   │   │   └── spine_05 [6]
│   │   │   │   │       ├── clavicle_l [7] ─── (왼팔 체인)
│   │   │   │   │       ├── clavicle_r [76] ── (오른팔 체인)
│   │   │   │   │       ├── neck_01 [145]
│   │   │   │   │       │   └── neck_02 [146]
│   │   │   │   │       │       └── head [147]
│   │   │   │   │       │           └── FACIAL_C_FacialRoot [271] (페이셜 본)
│   │   │   │   │       ├── spine_04_latissimus_l/r [162/163]
│   │   │   │   │       ├── clavicle_pec_l [164] (가슴 L)
│   │   │   │   │       │   └── breast_l [165] → breast_up/dn/fwd/in/out_l
│   │   │   │   │       ├── clavicle_pec_r [171] (가슴 R)
│   │   │   │   │       │   └── breast_r [172] → breast_dn/fwd/in/out/up_r
│   │   │   │   │       ├── hood_03_l [269] → hood_04_l [293]
│   │   │   │   │       └── hood_03_r [270] → hood_04_r [294]
│   │   │   │   └── (보정 본들)
│   │   │   │       ├── spine_cartilage_00-03 [306-317]
│   │   │   │       ├── spine_side_03_l/r [258/259]
│   │   │   │       ├── spine_bck_02/03 [180/257]
│   │   │   │       ├── spine_fwd_02/03 [260/179]
│   │   │   │       └── back_acc_rope [178] → back_acc_rope_tip [256]
│   │   │   └── spine_cartilage_04-06 [297-305]
│   ├── thigh_l [181] ── (왼다리 체인)
│   ├── thigh_r [215] ── (오른다리 체인)
│   ├── groin [249]
│   │   ├── groin_r [250]
│   │   └── groin_l [251]
│   ├── groin_volume [252]
│   └── outer_collision_root [267]
│       └── outer_collision [268]
├── prop_01_l [253]
├── prop_01_r [254]
├── SC_LinkTarget [255]
├── InteractionAnchor [288]
├── VB ik_root [318]
│   ├── VB ik_foot_l [320]
│   └── VB ik_foot_r [321]
└── VB Curves [319]
```

---

## 4. 왼팔 체인 (clavicle_l → hand_l)

```
clavicle_l [7]
├── upperarm_l [8]
│   ├── upperarm_twist_01_l [9] → upperarm_bck_01_l [10]
│   ├── upperarm_twist_02_l [11] → upperarm_volume_02_l [12]
│   ├── upperarm_twist_03_l [13]
│   ├── upperarm_twist_00_l [66]
│   ├── lowerarm_l [14]
│   │   ├── hand_l [15]
│   │   │   ├── thumb_01_l [16] → thumb_02_l [17] → thumb_03_l [18] → thumb_04_l [19]
│   │   │   │   └── (thumb_sub_02/03_l 보정)
│   │   │   ├── index_metacarpal_l [22] → index_01/02/03/04_l
│   │   │   ├── middle_metacarpal_l [30] → middle_01/02/03/04_l
│   │   │   ├── ring_metacarpal_l [38] → ring_01/02/03/04_l
│   │   │   ├── pinky_metacarpal_l [46] → pinky_01/02/03/04_l
│   │   │   └── hand_correctiveRoot_l [54]
│   │   │       ├── wrist_outer_l [55]
│   │   │       └── wrist_inner_l [56]
│   │   ├── lowerarm_twist_00/01/02/03_l [57,58,59,65]
│   │   └── lowerarm_correctiveRoot_l [60]
│   │       ├── lowerarm_bck_l [61]
│   │       ├── lowerarm_fwd_l [62]
│   │       ├── lowerarm_in_l [63]
│   │       └── lowerarm_out_l [64]
│   └── upperarm_correctiveRoot_l [67]
│       ├── upperarm_out_l [68]
│       ├── upperarm_in_l [69]
│       ├── upperarm_bck_l [70]
│       └── upperarm_fwd_l [71]
├── clavicle_out_l [72]
├── clavicle_scap_l [73]
├── clavicle_fwd_l [74]
├── armpit_l [75]
└── clavicle_hood_l [289]
```

오른팔은 동일 패턴 (인덱스 76 ~ 144, _r 접미사)

---

## 5. 왼다리 체인 (thigh_l → foot_l)

```
thigh_l [181]
├── calf_l [182]
│   ├── foot_l [183]
│   │   ├── ball_l [184] → tip_l [185]
│   │   ├── heel_l [186]
│   │   └── foot_correctiveRoot_l [187]
│   │       ├── foot_bck_l [188]
│   │       └── foot_fwd_l [189]
│   ├── calf_correctiveRoot_l [190]
│   │   ├── calf_knee_l [191]
│   │   └── calf_kneeBack_l [192]
│   ├── calf_twist_01/02/03_l [196,193,198]
│   │   └── (calf_bck/fwd 보정본들)
│   └── calf_twist_00_l [197]
├── thigh_correctiveRoot_l [200]
│   ├── thigh_fwd_l [201]
│   ├── thigh_out_l [202]
│   ├── thigh_bck_l [203]
│   │   ├── hip_01_l [204]
│   │   └── hip_02_l [205]
│   └── thigh_in_l [206]
└── thigh_twist_00/01/02/03_l [214,207,209,212]
    └── (thigh_bck/fwd 보정본들)
```

오른다리는 동일 패턴 (인덱스 215 ~ 248, _r 접미사)

---

## 6. 두부/경부 체인

```
neck_01 [145]
├── neck_02 [146]
│   ├── head [147]
│   │   ├── neck_03 [278]
│   │   ├── hood_head [279]
│   │   │   ├── hood_head_l/r [280/281]
│   │   │   ├── hood_head_01_l/r [291/292]
│   │   │   └── hood_head_mid [282]
│   │   │       ├── hood_head_top [283]
│   │   │       │   └── hood_head_back [284]
│   │   │       ├── hood_head_mid_l/r [285/286]
│   │   │       └── hood_head_front [287]
│   │   └── FACIAL_C_FacialRoot [271]
│   │       └── FACIAL_L/R_12IPV_UnderChin 2/4/6 [272-277]
│   └── FACIAL_C_Neck2Root [148]
│       ├── FACIAL_C_AdamsApple [149]
│       ├── FACIAL_L/R_NeckA1/2/3
└── FACIAL_C_Neck1Root [156]
    ├── FACIAL_C_NeckB [157]
    └── FACIAL_L/R_NeckB1/2
```

---

## 7. 무기 소켓 및 특수 본

```
root [0]
├── prop_01_l [253]  ← 왼손 무기 소켓
├── prop_01_r [254]  ← 오른손 무기 소켓
├── SC_LinkTarget [255]  ← 씬 컴포넌트 링크 타겟
└── InteractionAnchor [288]  ← 상호작용 앵커

lowerarm_weapon_02_l [295] ← lowerarm_twist_02_l 자식
lowerarm_weapon_02_r [296] ← lowerarm_twist_02_r 자식
```

---

## 8. 망토/케이프 체인

```
breast_l [165]
└── cape_string_00 [261]
    └── cape_string_01 [262]
        └── cape_string_02 [263]
            └── cape_string_03 [264]
                └── cape_string_04 [265]
                    └── cape_string_05 [266]
```

---

## 9. 척추 보정 본 (Cartilage)

```
spine_03 [4] 자식:
  spine_cartilage_04 [297] → L/R [298/299]
  spine_cartilage_05 [300] → L/R [301/302]
  spine_cartilage_06 [303] → L/R [304/305]

spine_02 [3] 자식:
  spine_cartilage_00 [306] → L/R [307/308]
  spine_cartilage_01 [309] → L/R [310/311]
  spine_cartilage_02 [312] → L/R [313/314]
  spine_cartilage_03 [315] → L/R [316/317]
```

---

## 10. 본 수 요약

| 그룹 | 본 수 (추정) |
|------|------------|
| 척추 (spine_01-05) | 5 |
| 왼팔 (clavicle → 손가락 포함) | ~75 |
| 오른팔 (동일) | ~75 |
| 왼다리 (thigh → foot) | ~34 |
| 오른다리 (동일) | ~34 |
| 두부/경부 | ~20 |
| 페이셜 (FACIAL_*) | ~14 |
| 가슴/브레스트 | ~12 |
| 후드/망토 | ~16 |
| 특수/소켓 본 | ~10 |
| 척추 보정 본 | ~21 |
| **총계** | **322** |
| 가상 본 (VB) | 4 |

---

## 11. PC_01 스켈레톤 에셋 목록

| 에셋명 | 경로 |
|--------|------|
| **PC_01_Body_001_Skeleton** | `/Game/Art/Character/PC/PC_01/Body/PC_01_Body_001/PC_01_Body_001_Skeleton` |
| CH_P_01_Head_001_Skeleton | `/Game/Art/Character/PC/PC_01/Head/CH_P_01_Head_001/` |
| PC_01_Weapon_01_Skeleton | `/Game/Art/Character/PC/PC_01/Weapon/PC_01_Weapon_01/` |
| PC_01_Weapon_01_Blade_Skeleton | `/Game/Art/Character/PC/PC_01/Weapon/PC_01_Weapon_01/` |
| Evie_hoodtestmesh_Skeleton | `/Game/Art/Character/PC/PC_01/Body/PC_01_Body_001/` (테스트용) |
