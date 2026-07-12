from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models_document import Document
from app.vector_store import get_qdrant_client
from services.embedding_service.service import get_service as get_embedding_service

from .bm25_index import BM25Index
from .classifier import classify_query, select_strategy
from .reranker import Reranker


class AdaptiveRetrieval:
    """Retrieval service implementing the TrustRAG adaptive strategy table."""

    def __init__(self):
        self.classifier = classify_query
        self.bm25 = BM25Index()
        self.reranker = Reranker()
        self._built = False
        self._chunks: List[Dict] = []

    def build_indices(self):
        db: Session = SessionLocal()
        try:
            docs = db.query(Document).all()
            chunks = []
            for doc in docs:
                text = doc.content or ''
                doc_chunks = [text[i:i + 1200] for i in range(0, len(text), 1200)] if text else []
                for index, chunk in enumerate(doc_chunks):
                    chunks.append({
                        'doc_id': doc.id,
                        'title': doc.title,
                        'filename': doc.filename,
                        'chunk_index': index,
                        'text': chunk,
                    })
            self.bm25.build(chunks)
            self._chunks = chunks
            self._built = True
        finally:
            db.close()

    def refresh(self):
        self._built = False
        self.build_indices()

    def _ensure_built(self):
        if not self._built:
            self.build_indices()

    def _dense_query(self, query: str, limit: int = 50) -> List[Dict]:
        try:
            vector = get_embedding_service().embed_texts([query])[0]
            hits = get_qdrant_client().search(collection_name='documents', query_vector=vector, limit=limit)
        except Exception:
            return []

        results = []
        for hit in hits:
            payload = hit.payload or {}
            score = float(hit.score)
            results.append({
                'doc_id': payload.get('doc_id'),
                'title': payload.get('title'),
                'filename': payload.get('filename'),
                'chunk_index': payload.get('chunk_index'),
                'text': payload.get('text'),
                'score': score,
                'similarity_score': score,
                'dense_score': score,
                'bm25_score': 0.0,
                'retrieval_method': 'dense',
            })
        return results

    def _bm25_query(self, query: str, limit: int = 50) -> List[Dict]:
        results = self.bm25.query(query, top_k=limit)
        for result in results:
            score = float(result.get('score', 0.0))
            result.pop('tokens', None)
            result['score'] = score
            result['similarity_score'] = score
            result['bm25_score'] = score
            result['dense_score'] = 0.0
            result['retrieval_method'] = 'bm25'
        return results

    def _merge_candidates(self, bm25_results: List[Dict], dense_results: List[Dict]) -> List[Dict]:
        candidates: Dict[tuple, Dict] = {}
        for result in bm25_results + dense_results:
            key = (result.get('doc_id'), result.get('chunk_index'))
            if key not in candidates:
                candidates[key] = result.copy()
            else:
                current = candidates[key]
                current['bm25_score'] = max(float(current.get('bm25_score', 0.0)), float(result.get('bm25_score', 0.0)))
                current['dense_score'] = max(float(current.get('dense_score', 0.0)), float(result.get('dense_score', 0.0)))
                current['text'] = current.get('text') or result.get('text')
                current['title'] = current.get('title') or result.get('title')

        merged = []
        for item in candidates.values():
            item['score'] = float(item.get('dense_score', 0.0)) + float(item.get('bm25_score', 0.0))
            item['similarity_score'] = item['score']
            item['retrieval_method'] = 'hybrid'
            merged.append(item)
        merged.sort(key=lambda item: item.get('score', 0.0), reverse=True)
        return merged

    def retrieve(self, query: str, top_k: int = 5, strategy: str = 'dense', rerank: Optional[bool] = None) -> Dict:
        self._ensure_built()
        strategy = strategy or 'dense'

        bm25_results = self._bm25_query(query, limit=50) if strategy in {'bm25', 'hybrid', 'hybrid_rerank'} else []
        dense_results = self._dense_query(query, limit=50) if strategy in {'dense', 'hybrid', 'hybrid_rerank'} else []

        if strategy == 'bm25':
            candidates = bm25_results
        elif strategy == 'dense':
            candidates = dense_results
        else:
            candidates = self._merge_candidates(bm25_results, dense_results)

        should_rerank = rerank if rerank is not None else strategy == 'hybrid_rerank'
        if should_rerank:
            results = self.reranker.rerank(query, candidates, top_k=top_k)
        else:
            results = candidates[:top_k]

        for result in results:
            result['retrieval_strategy'] = strategy
            result['reranked'] = bool(should_rerank)

        return {
            'strategy': strategy,
            'reranker_used': bool(should_rerank),
            'candidate_count': len(candidates),
            'results': results,
        }

    def baseline_query(self, query: str, top_k: int = 5) -> Dict:
        response = self.retrieve(query, top_k=top_k, strategy='dense', rerank=False)
        response['intent'] = 'baseline'
        response['phase'] = 'baseline_dense_rag'
        response['selection_reason'] = 'Baseline RAG uses dense vector retrieval for every query.'
        return response

    def hybrid_query(self, query: str, top_k: int = 5, rerank: bool = False) -> Dict:
        strategy = 'hybrid_rerank' if rerank else 'hybrid'
        response = self.retrieve(query, top_k=top_k, strategy=strategy, rerank=rerank)
        response['intent'] = 'fixed_hybrid'
        response['phase'] = 'fixed_hybrid_rag'
        response['selection_reason'] = 'Fixed Hybrid RAG uses lexical plus semantic retrieval for every query.'
        return response

    def query(self, query: str, top_k: int = 5) -> Dict:
        intent = self.classifier(query)
        strategy = select_strategy(intent)
        response = self.retrieve(query, top_k=top_k, strategy=strategy)
        response['intent'] = intent
        response['phase'] = 'adaptive_retrieval'
        response['selection_reason'] = (
            f"Intent '{intent}' selected '{strategy}' retrieval according to the TrustRAG adaptive strategy table."
        )
        return response


_service = None


def get_service():
    global _service
    if _service is None:
        _service = AdaptiveRetrieval()
    return _service
