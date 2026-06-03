import json
from server.tools.rag_search import rag_search


def test_search_returns_results():
    result = rag_search("keyword filter bypass password", top_k=3)
    data = json.loads(result)
    assert len(data["results"]) == 3
    assert data["query"] == "keyword filter bypass password"


def test_search_results_have_scores():
    result = rag_search("prompt injection", top_k=3)
    data = json.loads(result)
    for r in data["results"]:
        assert "score" in r
        assert 0 <= r["score"] <= 1


def test_search_relevant_to_query():
    result = rag_search("base64 encoding attack", top_k=5)
    data = json.loads(result)
    texts = " ".join(r.get("description", "") for r in data["results"]).lower()
    assert "encod" in texts or "base64" in texts or "obfuscat" in texts


def test_top_k_capped():
    result = rag_search("security", top_k=100)
    data = json.loads(result)
    assert len(data["results"]) <= 10
