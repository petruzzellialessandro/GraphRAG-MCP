import re
from rank_bm25 import BM25Okapi

class BM25Index:
    def __init__(self, chunks: list[dict]):
        # chunks: list of {"id": str, "text": str, ...}
        self.chunks = chunks
        tokenized = [self._tokenize(c["text"]) for c in chunks]
        self.bm25 = BM25Okapi(tokenized)

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"\w+", text.lower())

    def search(self, query: str, top_k: int = 10) -> list[tuple[dict, float]]:
        scores = self.bm25.get_scores(self._tokenize(query))
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
        return [(self.chunks[i], score) for i, score in ranked if score > 0]
