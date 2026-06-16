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

        