"""
LangGraph orchestrator for TrustRAG - coordinates multi-agent workflow
"""
from typing import Optional, List, Dict, Any
from .state import QueryState
from .agents import (
    QAAgent, SummaryAgent, CitationAgent, 
    VerificationAgent, ExplainabilityAgent, ReportAgent
)


class TrustRAGOrchestrator:
    """
    Coordinates all agents in a sequential workflow:
    1. QA Agent: Generate answer
    2. Citation Agent: Extract sources
    3. Verification Agent: Verify answer
    4. Summary Agent: Summarize documents
    5. Explainability Agent: Generate explanations
    6. Report Agent: Create final report
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.qa_agent = QAAgent(openai_api_key)
        self.summary_agent = SummaryAgent()
        self.citation_agent = CitationAgent()
        self.verification_agent = VerificationAgent()
        self.explainability_agent = ExplainabilityAgent()
        self.report_agent = ReportAgent()
    
    def process(self, state: QueryState) -> QueryState:
        """
        Execute the full agent pipeline
        """
        # Initialize state if needed
        if "explanations" not in state:
            state["explanations"] = []
        if "metadata" not in state:
            state["metadata"] = {}
        
        # Execute agents in sequence
        state = self.qa_agent.process(state)
        state = self.citation_agent.process(state)
        state = self.verification_agent.process(state)
        state = self.summary_agent.process(state)
        state = self.explainability_agent.process(state)
        state = self.report_agent.process(state)
        
        return state
    
    async def process_async(self, state: QueryState) -> QueryState:
        """
        Async version of process for integration with FastAPI
        """
        return self.process(state)


# Singleton instance
_orchestrator: Optional[TrustRAGOrchestrator] = None


def get_orchestrator(openai_api_key: Optional[str] = None) -> TrustRAGOrchestrator:
    """Get or create orchestrator singleton"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = TrustRAGOrchestrator(openai_api_key)
    return _orchestrator
