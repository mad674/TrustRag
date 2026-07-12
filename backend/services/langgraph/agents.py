"""
LangGraph agent implementations for TrustRAG
Each agent is a node in the StateGraph that processes queries
"""
import os
from typing import Optional, List, Dict, Any
from .state import QueryState


class QAAgent:
    """Question Answering agent - answers queries based on retrieved documents"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
    
    def process(self, state: QueryState) -> QueryState:
        """Process query and generate answer from retrieved documents"""
        query = state.get("query", "")
        retrieved_docs = state.get("retrieved_docs", [])

        if state.get("structured_answer"):
            return state
        
        if not retrieved_docs:
            state["structured_answer"] = "No relevant documents found for your query."
            state["confidence"] = 0.0
            return state
        
        answer = self._generate_answer(query, retrieved_docs)
        state["structured_answer"] = answer
        scores = [float(doc.get("score", 0.0)) for doc in retrieved_docs]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        state["confidence"] = max(0.05, min(0.95, 0.45 + avg_score * 0.5))
        
        return state
    
    def _generate_answer(self, query: str, docs: List[dict]) -> str:
        """Generate answer based on context and query"""
        if not docs:
            return f"I could not find information to answer: {query}"

        evidence = []
        for index, doc in enumerate(docs[:4], 1):
            text = " ".join(doc.get("text", "").split())
            if len(text) > 420:
                text = text[:420].rsplit(" ", 1)[0] + "..."
            title = doc.get("title") or f"Document {doc.get('doc_id', index)}"
            evidence.append(f"[{index}] {title}: {text}")

        return (
            f"TrustRAG found {len(docs)} relevant evidence passage(s) for: {query}\n\n"
            + "\n\n".join(evidence)
            + "\n\nSynthesis: this answer is grounded in the cited passages. "
            "Review the supporting evidence and confidence score before using it for high-stakes decisions."
        )


class SummaryAgent:
    """Summary agent - summarizes relevant documents"""
    
    def process(self, state: QueryState) -> QueryState:
        """Summarize retrieved documents"""
        retrieved_docs = state.get("retrieved_docs", [])
        
        if not retrieved_docs:
            state["explanations"].append("No documents to summarize")
            return state
        
        summary = self._summarize_docs(retrieved_docs)
        state["explanations"].append(f"Summary: {summary}")
        
        return state
    
    def _summarize_docs(self, docs: List[dict]) -> str:
        """Create a summary of documents"""
        texts = [doc.get("text", "")[:300] for doc in docs[:3]]
        combined = " ".join(texts)
        
        # Simple summary (first 150 chars)
        if len(combined) > 150:
            return combined[:150] + "..."
        return combined


class CitationAgent:
    """Citation agent - extracts and formats citations from sources"""
    
    def process(self, state: QueryState) -> QueryState:
        """Extract citations from retrieved documents"""
        if state.get("sources"):
            return state
        retrieved_docs = state.get("retrieved_docs", [])
        
        sources = []
        for doc in retrieved_docs:
            sources.append({
                "doc_id": doc.get("doc_id"),
                "title": doc.get("title", "Unknown"),
                "chunk_index": doc.get("chunk_index"),
                "relevance_score": doc.get("score", 0.0),
                "text_preview": doc.get("text", "")[:200]
            })
        
        state["sources"] = sources
        
        return state


class VerificationAgent:
    """Verification agent - verifies answer against source documents"""
    
    def process(self, state: QueryState) -> QueryState:
        """Verify answer against sources"""
        if state.get("verification_results"):
            return state
        answer = state.get("structured_answer", "")
        retrieved_docs = state.get("retrieved_docs", [])
        
        if not answer or not retrieved_docs:
            state["verification_results"] = {
                "is_grounded": False,
                "hallucination_risk": "high",
                "grounded_statements": []
            }
            return state
        
        # Check if answer references are grounded in documents
        verification = self._verify_answer(answer, retrieved_docs)
        state["verification_results"] = verification
        
        return state
    
    def _verify_answer(self, answer: str, docs: List[dict]) -> dict:
        """Verify answer is grounded in documents"""
        doc_texts = [doc.get("text", "").lower() for doc in docs]
        combined_text = " ".join(doc_texts)
        
        # Simple grounding check (in production would use LLM)
        answer_lower = answer.lower()
        grounded = any(word in combined_text for word in answer_lower.split() if len(word) > 3)
        
        return {
            "is_grounded": grounded,
            "hallucination_risk": "low" if grounded else "high",
            "evidence_score": 0.85 if grounded else 0.2,
            "grounded_statements": ["Answer is supported by retrieved documents"] if grounded else ["Unable to verify answer in documents"]
        }


class ExplainabilityAgent:
    """Explainability agent - generates explanations for the answer"""
    
    def process(self, state: QueryState) -> QueryState:
        """Generate explanations"""
        query = state.get("query", "")
        retrieved_docs = state.get("retrieved_docs", [])
        answer = state.get("structured_answer", "")
        
        explanations = [
            f"Query: {query}",
            f"Retrieved {len(retrieved_docs)} supporting passages",
            f"Answer confidence: {state.get('confidence', 0):.2%}",
            f"Retrieval intent: {state.get('intent') or 'qa'}",
            f"Retrieval strategy: {state.get('metadata', {}).get('retrieval_strategy', 'unknown')}",
            f"Reranker used: {state.get('metadata', {}).get('reranker_used', False)}",
        ]
        
        state["explanations"] = explanations
        
        return state


class ReportAgent:
    """Report agent - generates downloadable reports"""
    
    def process(self, state: QueryState) -> QueryState:
        """Generate final report"""
        if state.get("report"):
            return state
        query = state.get("query", "")
        answer = state.get("structured_answer", "")
        sources = state.get("sources", [])
        explanations = state.get("explanations", [])
        verification = state.get("verification_results", {})
        
        report = self._generate_report(query, answer, sources, explanations, verification)
        state["report"] = report
        
        return state
    
    def _generate_report(self, query: str, answer: str, sources: List[dict], 
                         explanations: List[str], verification: dict) -> str:
        """Generate a formatted report"""
        report_lines = [
            "="*60,
            "TRUSTRAG QUERY REPORT",
            "="*60,
            f"\nQuery: {query}",
            f"\nAnswer:\n{answer}",
            f"\n\nSources ({len(sources)} documents):",
        ]
        
        for i, source in enumerate(sources, 1):
            report_lines.append(f"  {i}. {source.get('title', 'Unknown')} (Score: {source.get('relevance_score', 0):.2f})")
        
        report_lines.extend([
            f"\nVerification Status: {'Grounded' if verification.get('is_grounded') else 'Not verified'}",
            f"Hallucination Risk: {verification.get('hallucination_risk', 'unknown').upper()}",
            "\nExplanations:",
        ])
        
        for exp in explanations:
            report_lines.append(f"  • {exp}")
        
        report_lines.append("\n" + "="*60)
        
        return "\n".join(report_lines)
