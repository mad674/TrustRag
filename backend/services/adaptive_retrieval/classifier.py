from typing import Literal

Intent = Literal['definition', 'comparison', 'summarization', 'citation', 'research_gap', 'qa']
Strategy = Literal['bm25', 'dense', 'hybrid', 'hybrid_rerank']

INTENT_STRATEGY: dict[str, Strategy] = {
    'definition': 'bm25',
    'comparison': 'hybrid',
    'summarization': 'dense',
    'research_gap': 'hybrid_rerank',
    'citation': 'dense',
    'qa': 'hybrid',
}


def classify_query(query: str) -> Intent:
    q = query.lower()
    if any(w in q for w in ['compare','vs','versus','difference','differences','contrast']):
        return 'comparison'
    if any(w in q for w in ['define','what is','meaning of','meaning','definition']):
        return 'definition'
    if any(w in q for w in ['summarize','summary','summarise','in summary','summation']):
        return 'summarization'
    if any(w in q for w in ['cite','citation','reference','references','source','sources']):
        return 'citation'
    if any(w in q for w in ['research gap','future work','open problem','limitations','gap']):
        return 'research_gap'
    return 'qa'


def select_strategy(intent: Intent) -> Strategy:
    return INTENT_STRATEGY.get(intent, 'hybrid')
