"""
LangGraph state definition for TrustRAG multi-agent orchestration
"""
from typing import TypedDict, List, Optional, Any
from dataclasses import field


class QueryState(TypedDict):
    """State passed through the agent graph"""
    query: str
    intent: Optional[str]
    retrieved_docs: List[dict]
    structured_answer: Optional[str]
    sources: List[dict]
    confidence: float
    explanations: List[str]
    verification_results: Optional[dict]
    report: Optional[str]
    metadata: dict
