import os
os.environ['HF_HUB_DISABLE_EXPERIMENTAL_WARNING'] = '1'
os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '0'

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import cast

import json

class RetrievalStore:

    def __init__(self):
        self.documents = []
        self.stopwords = {"the", "a", "is", "what", "how", "do", "you", "i", "it", "my", "me"}

    def add(self, text: str) -> None:
        self.documents.append(text)

    def _score(self, query: str, document: str) -> int:
        query_words = set(query.lower().split()) - self.stopwords
        doc_words = set(document.lower().split()) - self.stopwords
        return len(query_words & doc_words)

    def search(self, query: str, top_k: int = 3) -> list:
    	# similar to KNN
        scored = [
            (self._score(query, doc), doc)
            for doc in self.documents
        ]
        scored.sort(reverse=True)
        return [doc for score, doc in scored[:top_k] if score > 0]
  
class SemanticRetrievalStore:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.documents = []
        self.embeddings = []

    def add(self, text: str) -> None:
        embedding = self.model.encode(text)
        self.documents.append(text)
        self.embeddings.append(embedding)

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def search(self, query: str, top_k: int = 3) -> list:
        if not self.documents:
            return []
        
        query_embedding = self.model.encode(query)

        all_scored_docs = [
            (self._cosine_similarity(cast(np.ndarray,query_embedding), doc_embedding), doc)
            for doc_embedding, doc in zip(self.embeddings, self.documents)
        ]

        all_scored_docs.sort(reverse=True) # the higher the score, the lower the similarity

        return [doc for _, doc in all_scored_docs[:top_k]]

# ===========================
    def save(self, path: str) -> None:
        data = {
            "model_name": self.model_name,
            "documents": self.documents,
            "embeddings": [emb.tolist() for emb in self.embeddings]
        }
        with open(path, "w") as f:
            json.dump(data, f)

    @classmethod
    def load(cls, path: str, expected_model: str = "all-MiniLM-L6-v2") -> "SemanticRetrievalStore":
        with open(path, "r") as f:
            data = json.load(f)

        if data["model_name"] != expected_model:
            raise ValueError(
                f"Model mismatch: save file uses '{data['model_name']}', "
                f"but expected '{expected_model}'. Cannot load embeddings from a different model."
            )

        instance = cls(model_name=data["model_name"])
        instance.documents = data["documents"]
        instance.embeddings = [np.array(emb) for emb in data["embeddings"]]
        return instance

# ===========================

if __name__ == "__main__":
    store = SemanticRetrievalStore()
    store.add("My dog's name is Pickle")
    store.add("I work as a software engineer")
    store.add("My favorite food is pizza")

    import time
    start = time.time()
    results = store.search("What's my pet called?", top_k=2)
    print(f"Search took: {time.time() - start:.4f}s")
    print(results)


