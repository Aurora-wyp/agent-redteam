import json
import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

import config


class RAGIndexer:
    def __init__(self):
        self.model = SentenceTransformer(config.EMBEDDING_MODEL)
        self.dimension = 384
        self.index = None
        self.documents = []

    def load_data(self):
        docs = []

        for filename in ["attacks.json", "papers.json"]:
            path = os.path.join(config.RAG_DATA_DIR, filename)
            if not os.path.exists(path):
                continue
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                text = self._flatten(item)
                docs.append({"source": filename, "id": item.get("id", ""), "text": text, "raw": item})

        self.documents = docs
        return docs

    def _flatten(self, item: dict) -> str:
        parts = []
        for key in ["technique", "title", "name", "description", "summary", "category"]:
            if key in item and item[key]:
                parts.append(str(item[key]))
        if "examples" in item and isinstance(item["examples"], list):
            parts.extend(str(e) for e in item["examples"])
        if "known_strategies" in item and isinstance(item["known_strategies"], list):
            parts.extend(str(s) for s in item["known_strategies"])
        if "key_findings" in item and isinstance(item["key_findings"], list):
            parts.extend(str(f) for f in item["key_findings"])
        if "applicable_to" in item and isinstance(item["applicable_to"], list):
            parts.append("applicable to: " + ", ".join(str(a) for a in item["applicable_to"]))
        return " ".join(parts)

    def build_index(self):
        if not self.documents:
            self.load_data()
        texts = [d["text"] for d in self.documents]
        embeddings = self.model.encode(texts)
        faiss.normalize_L2(embeddings)
        self.index = faiss.IndexFlatIP(self.dimension)
        self.index.add(np.array(embeddings).astype("float32"))
        return len(self.documents)

    def save_index(self):
        os.makedirs(config.RAG_INDEX_DIR, exist_ok=True)
        path = os.path.join(config.RAG_INDEX_DIR, "knowledge.index")
        faiss.write_index(self.index, path)
        meta_path = os.path.join(config.RAG_INDEX_DIR, "documents.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2)

    def load_index(self):
        path = os.path.join(config.RAG_INDEX_DIR, "knowledge.index")
        meta_path = os.path.join(config.RAG_INDEX_DIR, "documents.json")
        if not os.path.exists(path) or not os.path.exists(meta_path):
            return False
        self.index = faiss.read_index(path)
        with open(meta_path, "r", encoding="utf-8") as f:
            self.documents = json.load(f)
        return True


if __name__ == "__main__":
    indexer = RAGIndexer()
    indexer.load_data()
    count = indexer.build_index()
    indexer.save_index()
    print(f"Index built: {count} documents")
