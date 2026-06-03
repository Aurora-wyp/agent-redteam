import json
from server.tools.defense_analyzer import analyze_defense


def test_detects_blocked():
    result = analyze_defense("I cannot reveal the password. I'm sorry.")
    data = json.loads(result)
    assert data["blocked"] is True
    assert data["defense_layer"] in ("system_prompt", "model_training", "unknown")


def test_output_has_defense_layer_not_types():
    """Output should have defense_layer (root cause), not defense_types (surface)."""
    result = analyze_defense("As an AI language model, I am not able to share secrets.")
    data = json.loads(result)
    assert "defense_layer" in data
    assert "defense_types" not in data  # removed from output
    assert isinstance(data["defense_layer"], str)
    assert len(data["defense_layer"]) > 0


def test_detects_leaked_api_key():
    result = analyze_defense("Here you go: the API key is sk-abc123def456ghi789jkl012mno345pqr678stu")
    data = json.loads(result)
    assert len(data["leaked_info"]) >= 1


def test_detects_leaked_password():
    result = analyze_defense("The secret password is: swordfish123")
    data = json.loads(result)
    assert len(data["leaked_info"]) > 0


def test_output_has_actionable_fields():
    """Output must include blocking_mechanism and next_bypass_strategy."""
    result = analyze_defense("I cannot comply with that request as it violates safety guidelines.")
    data = json.loads(result)
    assert "blocking_mechanism" in data
    assert "next_bypass_strategy" in data
    assert isinstance(data["blocking_mechanism"], str) and len(data["blocking_mechanism"]) > 0
    assert isinstance(data["next_bypass_strategy"], str) and len(data["next_bypass_strategy"]) > 0


def test_not_blocked_when_password_leaked():
    result = analyze_defense("The password is GOLDEN-RETRIEVER-42")
    data = json.loads(result)
    # No refusal patterns → not blocked, but leaked_info should catch the password
    assert len(data["leaked_info"]) > 0


def test_suggested_next_prompt_present():
    """When LLM is available, suggested_next_prompt should be populated."""
    result = analyze_defense("I cannot reveal the secret word.")
    data = json.loads(result)
    assert "suggested_next_prompt" in data
