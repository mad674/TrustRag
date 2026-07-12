"""
Evaluation metrics for TrustRAG - RAGAS-style evaluation
"""
from typing import List, Dict, Any
import numpy as np
from dataclasses import dataclass


@dataclass
class EvaluationMetrics:
    """Container for evaluation metrics"""
    precision_at_k: float
    recall_at_k: float
    mean_reciprocal_rank: float
    ndcg: float
    hallucination_rate: float
    context_relevance: float
    answer_relevance: float
    
    def to_dict(self) -> dict:
        return {
            "precision_at_k": self.precision_at_k,
            "recall_at_k": self.recall_at_k,
            "mean_reciprocal_rank": self.mean_reciprocal_rank,
            "ndcg": self.ndcg,
            "hallucination_rate": self.hallucination_rate,
            "context_relevance": self.context_relevance,
            "answer_relevance": self.answer_relevance,
        }


class EvaluationService:
    """Evaluate retrieval and generation quality"""
    
    @staticmethod
    def precision_at_k(retrieved: List[int], relevant: List[int], k: int = 10) -> float:
        """Calculate precision@k"""
        retrieved_k = retrieved[:k]
        relevant_set = set(relevant)
        if len(retrieved_k) == 0:
            return 0.0
        hits = sum(1 for doc_id in retrieved_k if doc_id in relevant_set)
        return hits / len(retrieved_k)
    
    @staticmethod
    def recall_at_k(retrieved: List[int], relevant: List[int], k: int = 10) -> float:
        """Calculate recall@k"""
        retrieved_k = retrieved[:k]
        relevant_set = set(relevant)
        if len(relevant_set) == 0:
            return 1.0
        hits = sum(1 for doc_id in retrieved_k if doc_id in relevant_set)
        return hits / len(relevant_set)
    
    @staticmethod
    def mean_reciprocal_rank(retrieved: List[int], relevant: List[int]) -> float:
        """Calculate Mean Reciprocal Rank"""
        relevant_set = set(relevant)
        for i, doc_id in enumerate(retrieved, 1):
            if doc_id in relevant_set:
                return 1.0 / i
        return 0.0
    
    @staticmethod
    def ndcg(relevance_scores: List[float], k: int = 10) -> float:
        """Calculate NDCG (Normalized Discounted Cumulative Gain)"""
        scores_k = relevance_scores[:k]
        if not scores_k:
            return 0.0
        
        # DCG
        dcg = sum(score / np.log2(i + 2) for i, score in enumerate(scores_k))
        
        # IDCG (ideal order)
        ideal_scores = sorted(relevance_scores, reverse=True)[:k]
        idcg = sum(score / np.log2(i + 2) for i, score in enumerate(ideal_scores))
        
        if idcg == 0:
            return 0.0
        return dcg / idcg
    
    @staticmethod
    def hallucination_rate(generated_text: str, context_texts: List[str]) -> float:
        """
        Estimate hallucination rate (simplified)
        Returns fraction of generated content not supported by context
        """
        if not generated_text or not context_texts:
            return 1.0
        
        # Simple heuristic: check word overlap
        gen_words = set(generated_text.lower().split())
        context_words = set(" ".join(context_texts).lower().split())
        
        supported = len(gen_words & context_words)
        if len(gen_words) == 0:
            return 0.0
        return 1.0 - (supported / len(gen_words))
    
    @staticmethod
    def context_relevance(retrieved_texts: List[str], query: str) -> float:
        """
        Measure how relevant retrieved context is to query (simplified)
        Uses keyword overlap as proxy
        """
        if not retrieved_texts:
            return 0.0
        
        query_words = set(query.lower().split())
        avg_overlap = 0.0
        
        for text in retrieved_texts:
            text_words = set(text.lower().split())
            if len(text_words) == 0:
                continue
            overlap = len(query_words & text_words) / len(query_words) if query_words else 0
            avg_overlap += overlap
        
        return avg_overlap / len(retrieved_texts) if retrieved_texts else 0.0
    
    @staticmethod
    def answer_relevance(answer: str, query: str) -> float:
        """
        Measure how relevant answer is to query (simplified)
        Uses semantic similarity proxy via word overlap
        """
        if not answer or not query:
            return 0.0
        
        query_words = set(query.lower().split())
        answer_words = set(answer.lower().split())
        
        if len(query_words) == 0 or len(answer_words) == 0:
            return 0.0
        
        overlap = len(query_words & answer_words)
        return min(overlap / len(query_words), 1.0)


class ExperimentRunner:
    """Run evaluation experiments"""
    
    def __init__(self, service: EvaluationService):
        self.service = service
        self.results: List[Dict[str, Any]] = []
    
    def run_evaluation(self, 
                      query: str,
                      retrieved_docs: List[dict],
                      relevant_doc_ids: List[int],
                      generated_answer: str) -> EvaluationMetrics:
        """Run full evaluation on single query"""
        
        retrieved_ids = [doc.get("doc_id") for doc in retrieved_docs]
        retrieved_texts = [doc.get("text", "") for doc in retrieved_docs]
        
        metrics = EvaluationMetrics(
            precision_at_k=self.service.precision_at_k(retrieved_ids, relevant_doc_ids),
            recall_at_k=self.service.recall_at_k(retrieved_ids, relevant_doc_ids),
            mean_reciprocal_rank=self.service.mean_reciprocal_rank(retrieved_ids, relevant_doc_ids),
            ndcg=self.service.ndcg([doc.get("score", 0.0) for doc in retrieved_docs]),
            hallucination_rate=self.service.hallucination_rate(generated_answer, retrieved_texts),
            context_relevance=self.service.context_relevance(retrieved_texts, query),
            answer_relevance=self.service.answer_relevance(generated_answer, query),
        )
        
        self.results.append({
            "query": query,
            "metrics": metrics.to_dict()
        })
        
        return metrics
    
    def get_aggregate_metrics(self) -> Dict[str, float]:
        """Calculate aggregate metrics across all experiments"""
        if not self.results:
            return {}
        
        metrics_list = [r["metrics"] for r in self.results]
        
        return {
            "avg_precision_at_k": np.mean([m["precision_at_k"] for m in metrics_list]),
            "avg_recall_at_k": np.mean([m["recall_at_k"] for m in metrics_list]),
            "avg_mrr": np.mean([m["mean_reciprocal_rank"] for m in metrics_list]),
            "avg_ndcg": np.mean([m["ndcg"] for m in metrics_list]),
            "avg_hallucination_rate": np.mean([m["hallucination_rate"] for m in metrics_list]),
            "avg_context_relevance": np.mean([m["context_relevance"] for m in metrics_list]),
            "avg_answer_relevance": np.mean([m["answer_relevance"] for m in metrics_list]),
            "total_queries": len(self.results),
        }
