"""
LangGraph orchestrator for TrustRAG - coordinates multi-agent workflow
"""
from typing import Optional, List, Dict, Any
from .state import QueryState
from .agents import (
    SupervisorAgent, QAAgent, SummaryAgent, ComparisonAgent, DefinitionAgent,
    CitationResponseAgent, CitationAgent, ResearchGapAgent,
    VerificationAgent, ExplainabilityAgent, ReportAgent,
    TaskRouterAgent, ClaimExtractionAgent, CorrectionSearchAgent,
)

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:
    StateGraph = None
    START = "__start__"
    END = "__end__"


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
        self.supervisor = SupervisorAgent()
        self.qa_agent = QAAgent(openai_api_key)
        self.summary_agent = SummaryAgent()
        self.comparison_agent = ComparisonAgent()
        self.definition_agent = DefinitionAgent()
        self.citation_response_agent = CitationResponseAgent()
        self.research_gap_agent = ResearchGapAgent()
        self.task_router = TaskRouterAgent()
        self.claim_extractor = ClaimExtractionAgent()
        self.correction_search = CorrectionSearchAgent()
        self.citation_agent = CitationAgent()
        self.verification_agent = VerificationAgent()
        self.explainability_agent = ExplainabilityAgent()
        self.report_agent = ReportAgent()
        self.graph = self._build_graph() if StateGraph is not None else None

    def _build_graph(self):
        graph = StateGraph(QueryState)
        graph.add_node("supervisor", self.supervisor.process)
        graph.add_node("task_router", self.task_router.process)
        graph.add_node("qa", self.qa_agent.process)
        graph.add_node("summary", self.summary_agent.process)
        graph.add_node("comparison", self.comparison_agent.process)
        graph.add_node("definition", self.definition_agent.process)
        graph.add_node("citation_response", self.citation_response_agent.process)
        graph.add_node("research_gap", self.research_gap_agent.process)
        graph.add_node("claims", self.claim_extractor.process)
        graph.add_node("citation", self.citation_agent.process)
        graph.add_node("verification", self.verification_agent.process)
        graph.add_node("correction_search", self.correction_search.process)
        graph.add_node("explainability", self.explainability_agent.process)
        graph.add_node("report", self.report_agent.process)
        graph.add_edge(START, "supervisor")
        graph.add_edge("supervisor", "task_router")
        graph.add_conditional_edges("task_router", lambda state: state.get("task", "qa"), {
            "qa": "qa", "summary": "summary", "comparison": "comparison",
            "definition": "definition", "citation_response": "citation_response",
            "research_gap": "research_gap",
        })
        graph.add_edge("qa", "claims")
        graph.add_edge("summary", "claims")
        graph.add_edge("comparison", "claims")
        graph.add_edge("definition", "claims")
        graph.add_edge("citation_response", "claims")
        graph.add_edge("research_gap", "claims")
        graph.add_edge("claims", "citation")
        graph.add_edge("citation", "verification")
        graph.add_conditional_edges("verification", self._verification_route, {
            "correction_search": "correction_search", "explainability": "explainability",
        })
        graph.add_conditional_edges("correction_search", self._task_route, {
            "qa": "qa", "summary": "summary", "comparison": "comparison",
            "definition": "definition", "citation_response": "citation_response",
            "research_gap": "research_gap",
        })
        graph.add_edge("explainability", "report")
        graph.add_edge("report", END)
        return graph.compile()

    @staticmethod
    def _verification_route(state: QueryState) -> str:
        verification = state.get("verification_results") or {}
        if verification.get("needs_correction_search") and state.get("refinement_iterations", 0) < 1:
            return "correction_search"
        return "explainability"

    @staticmethod
    def _task_route(state: QueryState) -> str:
        return state.get("task", "qa")

    def _run_task(self, state: QueryState) -> QueryState:
        agents = {
            "qa": self.qa_agent,
            "summary": self.summary_agent,
            "comparison": self.comparison_agent,
            "definition": self.definition_agent,
            "citation_response": self.citation_response_agent,
            "research_gap": self.research_gap_agent,
        }
        return agents.get(state.get("task", "qa"), self.qa_agent).process(state)
    
    def process(self, state: QueryState) -> QueryState:
        """
        Execute the full agent pipeline
        """
        # Initialize state if needed
        if "explanations" not in state:
            state["explanations"] = []
        if "metadata" not in state:
            state["metadata"] = {}
        state.setdefault("tool_calls", [])
        state.setdefault("agent_decisions", [])
        state.setdefault("claims", [])
        state.setdefault("refinement_iterations", 0)
        state.setdefault("correction_performed", False)
        state.setdefault("llm_provider", "fallback")
        
        if self.graph is not None:
            return self.graph.invoke(state)
        state = self.supervisor.process(state)
        state = self.task_router.process(state)
        task = state.get("task", "qa")
        state = self._run_task(state)
        state = self.claim_extractor.process(state)
        state = self.citation_agent.process(state)
        state = self.verification_agent.process(state)
        if (state.get("verification_results") or {}).get("needs_correction_search"):
            state = self.correction_search.process(state)
            if state.get("correction_performed"):
                state = self._run_task(state)
                state = self.claim_extractor.process(state)
                state = self.citation_agent.process(state)
                state = self.verification_agent.process(state)
        state = self.explainability_agent.process(state)
        return self.report_agent.process(state)
    
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
