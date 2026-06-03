import json
from server.tools.prompt_gen import generate_attack_prompts


def test_without_defense_analysis_returns_single_probe():
    """Without defense_analysis → single baseline probe, no AI guessing."""
    result = generate_attack_prompts(target="test-bot", context="a secret password", count=3)
    data = json.loads(result)
    assert data["mode"] == "baseline_probe"
    assert len(data["variants"]) == 1
    assert "password" in data["variants"][0]["prompt"].lower()


def test_with_defense_analysis_generates_multiple():
    """With defense_analysis → multiple targeted variants."""
    analysis = json.dumps({
        "blocked": True,
        "defense_types": ["refusal"],
        "defense_layer": "system_prompt",
        "blocking_mechanism": "Model refuses to discuss the password.",
    })
    result = generate_attack_prompts(
        target="test-bot",
        context="a password",
        count=3,
        defense_analysis=analysis,
    )
    data = json.loads(result)
    # Should be in targeted mode (LLM or fallback)
    assert data["mode"] in ("targeted", "targeted_fallback")
    assert len(data["variants"]) >= 1


def test_empty_defense_analysis_is_treated_as_missing():
    result = generate_attack_prompts(
        target="test", context="secret", count=3, defense_analysis=""
    )
    data = json.loads(result)
    assert data["mode"] == "baseline_probe"


def test_caps_at_max():
    analysis = json.dumps({"blocked": True, "defense_layer": "system_prompt"})
    result = generate_attack_prompts(
        target="test", context="secret", count=100, defense_analysis=analysis
    )
    data = json.loads(result)
    assert len(data["variants"]) <= 10


def test_target_in_result():
    result = generate_attack_prompts(target="my-chatbot", context="flag", count=2)
    data = json.loads(result)
    assert data["target"] == "my-chatbot"


def test_all_variants_have_prompt_and_technique():
    analysis = json.dumps({"blocked": True, "defense_layer": "external_censor_gpt"})
    result = generate_attack_prompts(
        target="test", context="secret", count=5, defense_analysis=analysis
    )
    data = json.loads(result)
    for v in data["variants"]:
        assert "prompt" in v
        assert "technique" in v
        assert len(v["prompt"]) > 0


def test_suggestion_included():
    result = generate_attack_prompts(target="test", context="password", count=3)
    data = json.loads(result)
    assert "suggestion" in data
    assert len(data["suggestion"]) > 0


def test_failed_prompts_accepted():
    """failed_prompts parameter should be accepted without error."""
    result = generate_attack_prompts(
        target="test",
        context="secret",
        count=3,
        failed_prompts='["prompt1", "prompt2"]',
    )
    data = json.loads(result)
    assert data["target"] == "test"
