import numpy as np
from sentence_transformers import SentenceTransformer

import config
from rag.indexer import RAGIndexer


class RAGRetriever:
    def __init__(self):
        self.model = SentenceTransformer(config.EMBEDDING_MODEL)
        self.indexer = RAGIndexer()
        if not self.indexer.load_index():
            self.indexer.load_data()
            self.indexer.build_index()
            self.indexer.save_index()

    def search(self, query: str, top_k: int = None) -> list:
        if top_k is None:
            top_k = config.TOP_K_DEFAULT

        query_embed = self.model.encode([query])
        query_embed = query_embed / np.linalg.norm(query_embed, axis=1, keepdims=True)

        scores, indices = self.indexer.index.search(
            np.array(query_embed).astype("float32"), k=min(top_k, len(self.indexer.documents))
        )

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.indexer.documents):
                continue
            doc = self.indexer.documents[idx]
            results.append({
                "score": float(score),
                "source": doc["source"],
                "id": doc["id"],
                "content": doc["text"][:500],
                "raw": doc["raw"],
            })

        return results

    def search_by_category(self, category: str) -> list:
        results = []
        for doc in self.indexer.documents:
            raw = doc.get("raw", {})
            if raw.get("category") == category:
                results.append(raw)
        return results


if __name__ == "__main__":
    retriever = RAGRetriever()
    results = retriever.search("How to bypass keyword filters and extract passwords?")
    for i, r in enumerate(results):
        print(f"\n--- Result {i+1} (score: {r['score']:.3f}) ---")
        print(f"Source: {r['source']}, ID: {r['id']}")
        print(r["content"][:300])
