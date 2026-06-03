"""rag_search tool — RAG-based knowledge retrieval for attack techniques."""

import json

from rag.retriever import RAGRetriever

_retriever = None


def _get_retriever() -> RAGRetriever:
    global _retriever
    if _retriever is None:
        _retriever = RAGRetriever()
    return _retriever


def rag_search(query: str, top_k: int = 5) -> str:
    """Search the attack knowledge base using RAG.

    Args:
        query: Natural language query about attack techniques or defenses
        top_k: Number of results to return (1-10)
    """
    top_k = min(max(top_k, 1), 10)
    retriever = _get_retriever()
    results = retriever.search(query, top_k=top_k)

    output = []
    for r in results:
        output.append({
            "score": round(r["score"], 3),
            "source": r["source"],
            "technique": r["raw"].get("technique") or r["raw"].get("name", ""),
            "category": r["raw"].get("category", ""),
            "description": r["raw"].get("description") or r["raw"].get("summary", ""),
            "examples": r["raw"].get("examples", [])[:2] if "examples" in r["raw"] else [],
            "strategies": r["raw"].get("known_strategies", [])[:3] if "known_strategies" in r["raw"] else [],
        })

    return json.dumps({"query": query, "results": output}, ensure_ascii=False, indent=2)
