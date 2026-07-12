from typing import List, Dict
from rank_bm25 import BM25Okapi
import re

class BM25Index:
    def __init__(self):
        self.documents = []  # list of dicts: {doc_id, chunk_index, text, tokens}
        self.bm25 = None

    def _tokenize(self, text: str) -> List[str]:
        # simple tokenizer
        tokens = re.findall(r"\w+", text.lower())
        return tokens

    def build(self, chunks: List[Dict]):
        # chunks: list of {doc_id, chunk_index, text}
        self.documents = []
        corpus = []
        for c in chunks:
            tokens = self._tokenize(c['text'])
            self.documents.append({**c, 'tokens': tokens})
            corpus.append(tokens)
        if corpus:
            self.bm25 = BM25Okapi(corpus)
        else:
            self.bm25 = None

    def query(self, query: str, top_k: int = 10):
        if not self.bm25:
            return []
        tokens = self._tokenize(query)
        scores = self.bm25.get_scores(tokens)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
        results = []
        for idx, score in ranked:
            doc = self.documents[idx]
            results.append({**doc, 'score': float(score)})
        return results
