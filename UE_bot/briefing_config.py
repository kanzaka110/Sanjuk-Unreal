"""브리핑 설정 — 상수, 카테고리, 태그 정의."""

from __future__ import annotations

CATEGORIES: list[str] = [
    "Animation Blueprint",
    "Control Rig",
    "Motion Matching",
    "UAF/AnimNext",
    "MetaHuman",
    "Sequencer",
    "Live Link",
    "ML Deformer",
    "GASP",
    "Mover Plugin",
    "AI Animation Tech",
    "Physics/Simulation",
    "GitHub/Open Source",
]

VALID_TAGS: list[str] = [
    "Procedural Animation", "IK", "Retargeting", "Physics",
    "Facial Animation", "Locomotion", "State Machine", "Blend Space",
    "Morph Target", "Root Motion", "Ragdoll", "Cloth Simulation",
    "Motion Capture", "Skeletal Mesh", "Vertex Animation",
    "AI/ML", "GitHub", "Neural Animation", "Diffusion", "NeRF",
]

DIFFICULTY_LEVELS = ["초급", "중급", "고급"]
UE_VERSIONS = ["5.5", "5.6", "5.7", "5.8+"]

# 6개 검색 카테고리 (다중소스 검색용)
SEARCH_SOURCES: dict[str, list[str]] = {
    "공식": [
        "site:unrealengine.com animation",
        "site:dev.epicgames.com animation workflow",
        "site:forums.unrealengine.com animation",
    ],
    "커뮤니티": [
        "site:reddit.com/r/unrealengine animation",
        "site:80.lv unreal animation",
        "Unreal Engine animation Discord community",
    ],
    "뉴스": [
        "site:cgchannel.com Unreal Engine animation",
        "site:awn.com Unreal Engine",
        "site:creativebloq.com Unreal Engine",
    ],
    "GitHub": [
        "site:github.com unreal engine animation plugin",
        "github UE5 animation tool new release",
    ],
    "교육": [
        "Unreal Engine technical animation tutorial",
        "site:youtube.com UE5 animation tutorial",
    ],
}
