from pathlib import Path


def test_unreal_router_v2_has_provider_specific_public_roles_and_external_state():
    from UE_bot import model_router

    assert model_router.POLICY_VERSION == "unreal-briefing-model-router.v2"
    expected = {
        "PUBLIC_RESEARCH": ("perplexity", "public_evidence"),
        "FACT_EXTRACTION": ("codex", "public_editorial"),
        "METADATA": ("codex", "public_editorial"),
        "BODY_GENERATION": ("codex", "public_editorial"),
        "TREND_ANALYSIS": ("grok", "public_analysis"),
        "CROSS_ANALYSIS": ("grok", "public_analysis"),
    }
    for stage, (provider, authority) in expected.items():
        cfg = model_router.POLICY["stages"][stage]
        assert cfg["provider"] == provider
        assert cfg["authority"] == authority
        assert cfg["fallback"] is None
    assert model_router.DEFAULT_STATE_DIR == Path("/home/kanzaka110/.local/state/sanjuk-briefing-router/unreal")
    assert "UE_bot/data" not in str(model_router.DEFAULT_STATE_DIR)
