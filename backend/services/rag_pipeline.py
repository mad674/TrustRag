import math
import re
from typing import Dict, List, Optional

from services.adaptive_retrieval.service import get_service as get_retrieval_service


def _tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-zA-Z0-9_]+", text.lower()) if len(token) > 2}


def _clip(text: str, limit: int = 420) -> str:
    normalized = " ".join((text or "").split())
    if len(normalized) <= limit:
        return normalized
    return normalized[:limit].rsplit(" ", 1)[0] + "..."


class AnswerGenerator:
    """Local grounded answer generator used when no external LLM key is configured."""

    def generate(self, query: str, contexts: List[Dict], intent: Optional[str] = None) -> str:
        if not contexts:
            return "No relevant evidence was found in the uploaded corpus."

        if intent == "summarization":
            passages = " ".join(_clip(item.get("text", ""), 260) for item in contexts[:5])
            return f"Summary based on retrieved evidence: {_clip(passages, 900)}"

        if intent == "citation":
            lines = []
            for index, item in enumerate(contexts[:5], 1):
                title = item.get("title") or f"Document {item.get('doc_id', index)}"
                lines.append(f"[{index}] {title}, chunk {item.get('chunk_index', 0)}.")
            return "Relevant citation candidates:\n" + "\n".join(lines)

        if intent == "research_gap":
            evidence = " ".join(_clip(item.get("text", ""), 220) for item in contexts[:6])
            return (
                "Potential research gaps and future-work signals found in the corpus: "
                f"{_clip(evidence, 1000)}"
            )

        evidence_lines = []
        for index, item in enumerate(contexts[:4], 1):
            title = item.get("title") or f"Document {item.get('doc_id', index)}"
            evidence_lines.append(f"[{index}] {title}: {_clip(item.get('text', ''))}")

        return (
            f"Answer for: {query}\n\n"
            + "\n\n".join(evidence_lines)
            + "\n\nGrounded synthesis: the response is derived from the supporting chunks above."
        )


class EvidenceVerifier:
    """Computes evidence overlap, hallucination risk, and confidence from retrieved chunks."""

    def verify(self, query: str, answer: str, contexts: List[Dict]) -> Dict:
        if not contexts:
            return {
                "is_grounded": False,
                "evidence_score": 0.0,
                "hallucination_score": 1.0,
                "hallucination_risk": "high",
                "matched_terms": [],
                "unsupported_terms": sorted(_tokens(answer))[:20],
            }

        answer_terms = _tokens(answer) - _tokens(query)
        evidence_terms = set()
        for context in contexts:
            evidence_terms |= _tokens(context.get("text", ""))

        matched = sorted(answer_terms & evidence_terms)
        unsupported = sorted(answer_terms - evidence_terms)
        evidence_score = len(matched) / max(1, len(answer_terms))
        avg_similarity = sum(float(item.get("similarity_score", item.get("score", 0.0))) for item in contexts)
        avg_similarity = avg_similarity / max(1, len(contexts))
        normalized_similarity = 1 - math.exp(-max(0.0, avg_similarity))
        confidence = max(0.0, min(0.98, 0.55 * evidence_score + 0.35 * normalized_similarity + 0.10))
        hallucination_score = 1.0 - evidence_score

        if confidence >= 0.72:
            risk = "low"
        elif confidence >= 0.45:
            risk = "medium"
        else:
            risk = "high"

        return {
            "is_grounded": evidence_score >= 0.35,
            "evidence_score": round(evidence_score, 4),
            "confidence": round(confidence, 4),
            "hallucination_score": round(hallucination_score, 4),
            "hallucination_risk": risk,
            "matched_terms": matched[:30],
            "unsupported_terms": unsupported[:30],
        }


class TrustRAGPipeline:
    def __init__(self):
        self.retrieval = get_retrieval_service()
        self.generator = AnswerGenerator()
        self.verifier = EvidenceVerifier()

    def run(self, query: str, top_k: int = 5, mode: str = "adaptive") -> Dict:
        if mode == "baseline":
            retrieval = self.retrieval.baseline_query(query, top_k=top_k)
        elif mode == "hybrid":
            retrieval = self.retrieval.hybrid_query(query, top_k=top_k, rerank=False)
        elif mode == "hybrid_rerank":
            retrieval = self.retrieval.hybrid_query(query, top_k=top_k, rerank=True)
        else:
            retrieval = self.retrieval.query(query, top_k=top_k)

        contexts = retrieval.get("results", [])
        answer = self.generator.generate(query, contexts, retrieval.get("intent"))
        verification = self.verifier.verify(query, answer, contexts)
        confidence = verification.get("confidence", 0.0)

        sources = [
            {
                "doc_id": item.get("doc_id"),
                "title": item.get("title", "Unknown"),
                "filename": item.get("filename"),
                "chunk_index": item.get("chunk_index"),
                "similarity_score": item.get("similarity_score", item.get("score", 0.0)),
                "relevance_score": item.get("score", 0.0),
                "retrieval_strategy": item.get("retrieval_strategy", retrieval.get("strategy")),
                "text_preview": _clip(item.get("text", ""), 260),
            }
            for item in contexts
        ]

        explanations = [
            retrieval.get("selection_reason", ""),
            f"Pipeline phase: {retrieval.get('phase')}",
            f"Retrieved {len(contexts)} supporting chunk(s) from {retrieval.get('candidate_count', len(contexts))} candidate(s).",
            f"Evidence score: {verification.get('evidence_score', 0.0):.2f}; hallucination score: {verification.get('hallucination_score', 1.0):.2f}.",
        ]

        report = self._report(query, answer, retrieval, verification, sources)
        return {
            "query": query,
            "mode": mode,
            "phase": retrieval.get("phase"),
            "intent": retrieval.get("intent"),
            "retrieval_strategy": retrieval.get("strategy"),
            "reranker_used": retrieval.get("reranker_used", False),
            "answer": answer,
            "sources": sources,
            "supporting_chunks": contexts,
            "confidence": confidence,
            "verification": verification,
            "explanations": explanations,
            "report": report,
        }

    def _report(self, query: str, answer: str, retrieval: Dict, verification: Dict, sources: List[Dict]) -> str:
        lines = [
            "TRUSTRAG QUERY REPORT",
            f"Query: {query}",
            f"Intent: {retrieval.get('intent')}",
            f"Retrieval Strategy: {retrieval.get('strategy')}",
            f"Reranker Used: {retrieval.get('reranker_used')}",
            f"Confidence: {verification.get('confidence', 0.0):.2%}",
            f"Evidence Score: {verification.get('evidence_score', 0.0):.2%}",
            f"Hallucination Risk: {verification.get('hallucination_risk', 'unknown')}",
            "",
            "Answer:",
            answer,
            "",
            "Sources:",
        ]
        for index, source in enumerate(sources, 1):
            lines.append(
                f"{index}. {source.get('title')} | chunk {source.get('chunk_index')} | score {float(source.get('relevance_score', 0.0)):.4f}"
            )
        return "\n".join(lines)


_pipeline = None


def get_pipeline() -> TrustRAGPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = TrustRAGPipeline()
    return _pipeline
