from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models_document import Document
from services.dense.retriever import DenseRetriever
from services.hybrid.retriever import HybridRetriever
from services.reranker.service import CrossEncoderReranker

from .bm25_index import BM25Index
from .classifier import classify_query, select_strategy


class AdaptiveRetrieval:
    """Retrieval service implementing the TrustRAG adaptive strategy table."""

    def __init__(self):
        self.classifier = classify_query
        self.bm25 = BM25Index()
        self.dense = DenseRetriever()
        self.hybrid = HybridRetriever()
        self.reranker = CrossEncoderReranker()
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
                        'doc_id': str(doc.id),
                        'owner_id': str(doc.uploaded_by) if doc.uploaded_by else None,
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

    def _dense_query(self, query: str, limit: int = 50, owner_id: Optional[str] = None) -> List[Dict]:
        try:
            return self.dense.retrieve(query, limit=limit, owner_id=owner_id)
        except Exception:
            return []

    def _bm25_query(self, query: str, limit: int = 50, owner_id: Optional[str] = None) -> List[Dict]:
        results = self.bm25.query(query, top_k=limit)
        if owner_id:
            results = [item for item in results if item.get('owner_id') == owner_id]
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

    def retrieve(self, query: str, top_k: int = 5, strategy: str = 'dense', rerank: Optional[bool] = None, owner_id: Optional[str] = None) -> Dict:
        self._ensure_built()
        strategy = strategy or 'dense'

        bm25_results = self._bm25_query(query, limit=50, owner_id=owner_id) if strategy in {'bm25', 'hybrid', 'hybrid_rerank'} else []
        dense_results = self._dense_query(query, limit=50, owner_id=owner_id) if strategy in {'dense', 'hybrid', 'hybrid_rerank'} else []

        if strategy == 'bm25':
            candidates = bm25_results
        elif strategy == 'dense':
            candidates = dense_results
        else:
            candidates = self.hybrid.retrieve(bm25_results, dense_results, top_k=50)

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
            'reranking_explanation': (
                'Candidates were rescored by the configured Cross-Encoder.'
                if should_rerank and self.reranker.model is not None
                else 'Candidates were rescored by the local normalized embedding fallback.'
                if should_rerank
                else 'Reranking was not selected for this retrieval strategy.'
            ),
            'results': results,
        }

    def baseline_query(self, query: str, top_k: int = 5, owner_id: Optional[str] = None) -> Dict:
        response = self.retrieve(query, top_k=top_k, strategy='dense', rerank=False, owner_id=owner_id)
        response['intent'] = 'baseline'
        response['phase'] = 'baseline_dense_rag'
        response['selection_reason'] = 'Baseline RAG uses dense vector retrieval for every query.'
        return response

    def hybrid_query(self, query: str, top_k: int = 5, rerank: bool = False, owner_id: Optional[str] = None) -> Dict:
        strategy = 'hybrid_rerank' if rerank else 'hybrid'
        response = self.retrieve(query, top_k=top_k, strategy=strategy, rerank=rerank, owner_id=owner_id)
        response['intent'] = 'fixed_hybrid'
        response['phase'] = 'fixed_hybrid_rag'
        response['selection_reason'] = 'Fixed Hybrid RAG uses lexical plus semantic retrieval for every query.'
        return response

    def query(self, query: str, top_k: int = 5, owner_id: Optional[str] = None) -> Dict:
        intent = self.classifier(query)
        strategy = select_strategy(intent)
        response = self.retrieve(query, top_k=top_k, strategy=strategy, owner_id=owner_id)
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
